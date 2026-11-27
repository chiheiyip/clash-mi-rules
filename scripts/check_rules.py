#!/usr/bin/env python3
"""clash-mi-rules rule-source URL availability check.

Scans every *.yaml at repo root, extracts all rule-provider URLs, the
geox-url GEO database URLs and the health-check probe URL, and verifies each
returns HTTP 2xx/3xx.

This is the "rules URL 可用性检查" that CI runs on schedule so a silently
broken mirror (e.g. gh-proxy.com outage) surfaces instead of only failing on
deployment day.

gh-proxy.com occasionally rate-limits CI runners (403). Each URL is therefore
retried with backoff; if the primary mirror still fails, the same path is
tried on the backup mirror documented in the configs. A URL that only works
on the backup mirror is reported as a warning (the configs still point at the
primary, so switching may be needed) but does not fail the run.

Usage:
    python3 scripts/check_rules.py [--timeout 15] [--retries 3] [config.yaml ...]

Exit code 0 = every URL reachable (possibly via the backup mirror).
Non-zero = at least one URL unreachable on every mirror.
"""
import argparse
import concurrent.futures as cf
import glob
import os
import sys
import time
import urllib.error
import urllib.request

import yaml

PRIMARY_PREFIX = "https://gh-proxy.com/"
BACKUP_PREFIX = "https://ghproxy.freeapp.tech/"
HEALTH_URL = "http://www.gstatic.com/generate_204"
RETRYABLE_HTTP = {403, 408, 429, 500, 502, 503, 504}

UA = ("clash-mi-rules-ci/1.0 (+https://github.com/chiheiyip/clash-mi-rules) "
      "(rule-source availability check)")

IN_GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"


def collect_urls(paths):
    urls = set()
    for p in paths:
        try:
            data = yaml.safe_load(open(p, encoding="utf-8"))
        except Exception:  # validate.py reports the parse error; skip here
            continue
        for cfg in (data.get("rule-providers") or {}).values():
            u = (cfg or {}).get("url")
            if u and u.startswith(("https://", "http://")):
                urls.add(u)
        for u in (data.get("geox-url") or {}).values():
            if isinstance(u, str) and u.startswith(("https://", "http://")):
                urls.add(u)
    # always also probe the latency/health URL so a broken probe target is caught
    urls.add(HEALTH_URL)
    return urls


def probe_once(url, timeout):
    """One HEAD (falling back to a 1-byte ranged GET). Returns (ok, info, retryable)."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 400, f"{r.status}", False
    except urllib.error.HTTPError as e:
        if e.code not in (403, 405):
            return False, f"HTTP {e.code}", e.code in RETRYABLE_HTTP
        # some mirrors reject HEAD: retry as a ranged GET so large lists aren't downloaded
        try:
            g = urllib.request.Request(url, headers={"User-Agent": UA, "Range": "bytes=0-0"})
            with urllib.request.urlopen(g, timeout=timeout) as r:
                return r.status < 400, f"GET {r.status}", False
        except urllib.error.HTTPError as e2:
            return False, f"HEAD {e.code} / GET {e2.code}", e2.code in RETRYABLE_HTTP
        except Exception as e2:  # noqa: BLE001
            return False, f"HEAD {e.code} / GET {type(e2).__name__}", True
    except Exception as e:  # noqa: BLE001  (timeouts, resets, DNS)
        return False, f"{type(e).__name__}: {e}", True


def probe(url, timeout, retries):
    info = ""
    for attempt in range(retries):
        ok, info, retryable = probe_once(url, timeout)
        if ok or not retryable:
            return ok, info
        if attempt + 1 < retries:
            time.sleep(2 ** (attempt + 1))
    return False, info


def check(url, timeout, retries):
    """Returns (url, status, info) with status in {"ok", "backup", "bad"}."""
    ok, info = probe(url, timeout, retries)
    if ok:
        return url, "ok", info
    if url.startswith(PRIMARY_PREFIX):
        alt = BACKUP_PREFIX + url[len(PRIMARY_PREFIX):]
        alt_ok, alt_info = probe(alt, timeout, retries)
        if alt_ok:
            return url, "backup", f"primary: {info}; backup mirror: {alt_info}"
        return url, "bad", f"primary: {info}; backup mirror: {alt_info}"
    return url, "bad", info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("configs", nargs="*")
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = args.configs or sorted(glob.glob(os.path.join(repo, "*.yaml")))
    urls = sorted(collect_urls(paths))
    if not urls:
        print("no URLs found to check")
        return 1

    counts = {"ok": 0, "backup": 0, "bad": 0}
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        futs = [pool.submit(check, u, args.timeout, args.retries) for u in urls]
        for fut in cf.as_completed(futs):
            url, status, info = fut.result()
            counts[status] += 1
            label = {"ok": "ok    ", "backup": "BACKUP", "bad": "BAD   "}[status]
            print(f"[{label}] {url}  ({info})")
            if IN_GITHUB_ACTIONS and status == "backup":
                print(f"::warning title=Primary mirror failed::{url} only reachable via {BACKUP_PREFIX}")
            elif IN_GITHUB_ACTIONS and status == "bad":
                print(f"::error title=Rule source unreachable::{url} ({info})")

    print(f"\n{counts['ok']} OK / {counts['backup']} via backup mirror / "
          f"{counts['bad']} BAD of {len(urls)} URL(s)")
    return 1 if counts["bad"] else 0


if __name__ == "__main__":
    sys.exit(main())
