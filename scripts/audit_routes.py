#!/usr/bin/env python3
"""clash-mi-rules routing audit: simulate Mihomo first-match against the real upstream lists.

Upstream rule lists change without notice. A list for one service can start to
include a domain shared by many websites (payment, login, CAPTCHA), and every
site that embeds it then gets that request routed through a different group /
exit IP than the page itself -> CAPTCHAs never pass, payments get flagged.
This happened with blackmatrix7's Copilot.list (stripe.com, auth0.com,
challenges.cloudflare.com, ...).

This script downloads the current content of every domain / classical
rule-provider in the config, replays the `rules:` list top-down for each
domain in scripts/route_expectations.txt, and fails if any domain lands in a
group other than the expected one(s).

Only domain matching is simulated (DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD and
domain rule sets). IP rules are skipped: in this config they all carry
no-resolve, so they never apply to connections that have a domain.

Usage:
    python3 scripts/audit_routes.py [--config clash-mi-detail.yaml]
                                    [--expect scripts/route_expectations.txt]

Exit code 0 = every expectation holds. Non-zero = mismatch or download failure.
"""
import argparse
import concurrent.futures as cf
import os
import re
import sys
import time
import urllib.request

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR_PREFIXES = ("https://gh-proxy.com/", "https://ghproxy.freeapp.tech/")
MRS_RE = re.compile(r"/meta-rules-dat/raw/refs/heads/meta/geo/(geosite|geoip)/(.+)\.mrs$")
UA = "clash-mi-rules-ci/1.0 (+https://github.com/chiheiyip/clash-mi-rules) (routing audit)"


def raw_url(url):
    """Map a configured provider URL to a plain-text source on raw.githubusercontent.com."""
    m = MRS_RE.search(url)
    if m:  # binary .mrs -> the .list text file published next to it
        return f"https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/{m.group(1)}/{m.group(2)}.list"
    for p in MIRROR_PREFIXES:
        if url.startswith(p):
            return "https://" + url[len(p):]
    return url


def fetch(url, retries=3, timeout=60):
    err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"{url}: {err}")


def parse(text, behavior):
    exact, suffix, keyword = set(), set(), []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith("payload"):
            continue
        if behavior == "domain":
            if ln.startswith("+."):
                suffix.add(ln[2:])
            elif ln.startswith("."):
                suffix.add(ln[1:])
            else:
                exact.add(ln)
        else:  # classical
            parts = [p.strip() for p in ln.split(",")]
            if len(parts) < 2:
                continue
            t, v = parts[0], parts[1]
            if t == "DOMAIN":
                exact.add(v)
            elif t == "DOMAIN-SUFFIX":
                suffix.add(v)
            elif t == "DOMAIN-KEYWORD":
                keyword.append(v)
    return exact, suffix, keyword


def build_rules(cfg):
    providers = cfg.get("rule-providers") or {}
    needed = {}
    for r in cfg["rules"]:
        parts = [p.strip() for p in r.split(",")]
        if parts[0] == "RULE-SET":
            p = providers[parts[1]]
            if p.get("behavior") in ("domain", "classical"):
                needed[parts[1]] = p
    with cf.ThreadPoolExecutor(6) as pool:
        futs = {name: pool.submit(fetch, raw_url(p["url"])) for name, p in needed.items()}
        content = {name: f.result() for name, f in futs.items()}

    rules = []
    for r in cfg["rules"]:
        parts = [p.strip() for p in r.split(",")]
        t = parts[0]
        exact, suffix, keyword = set(), set(), []
        if t == "MATCH":
            target = parts[1]
        else:
            target = parts[2]
            if t == "RULE-SET" and parts[1] in content:
                exact, suffix, keyword = parse(content[parts[1]], needed[parts[1]]["behavior"])
            elif t == "DOMAIN":
                exact.add(parts[1])
            elif t == "DOMAIN-SUFFIX":
                suffix.add(parts[1])
            elif t == "DOMAIN-KEYWORD":
                keyword.append(parts[1])
            else:  # IP rules (all no-resolve) and anything else never match a domain
                pass
        rules.append({"text": r, "type": t, "target": target,
                      "exact": exact, "suffix": suffix, "keyword": keyword})
    return rules


def first_match(rules, domain):
    labels = domain.split(".")
    suffixes = {".".join(labels[k:]) for k in range(len(labels))}
    for i, ru in enumerate(rules):
        if ru["type"] == "MATCH":
            return i
        if domain in ru["exact"] or suffixes & ru["suffix"] or any(k in domain for k in ru["keyword"]):
            return i
    return len(rules) - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(REPO, "clash-mi-detail.yaml"))
    ap.add_argument("--expect", default=os.path.join(REPO, "scripts", "route_expectations.txt"))
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    try:
        rules = build_rules(cfg)
    except RuntimeError as e:
        print(f"[error] could not download a rule list: {e}")
        return 2

    bad = 0
    total = 0
    for ln in open(args.expect, encoding="utf-8"):
        ln = ln.split("#", 1)[0].strip()
        if not ln:
            continue
        # group names may contain spaces ("Stream Media"): domain = first token, rest = groups
        domain, expected = ln.split(None, 1)
        expected = expected.strip()
        allowed = {g.strip() for g in expected.split("|")}
        i = first_match(rules, domain)
        got = rules[i]["target"]
        total += 1
        if got in allowed:
            print(f"[ok    ] {domain:42s} -> {got}")
        else:
            bad += 1
            print(f"[WRONG ] {domain:42s} -> {got}  (expected {expected}; matched rule #{i + 1}: {rules[i]['text']})")
            if os.environ.get("GITHUB_ACTIONS") == "true":
                print(f"::error title=Routing expectation failed::{domain} -> {got} "
                      f"(expected {expected}) via {rules[i]['text']}")
    print(f"\n{total - bad}/{total} routing expectations hold.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
