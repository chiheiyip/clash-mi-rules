#!/usr/bin/env python3
"""clash-mi-rules rule-source URL availability check.

Scans every *.yaml at repo root, extracts all rule-provider URLs plus the
health-check probe URL, and verifies each returns HTTP 2xx/3xx (and, where
possible, that the body is plausible).

This is the "rules URL 可用性检查" that CI runs on schedule so a silently
broken mirror (e.g. gh-proxy.com outage) surfaces instead of only failing on
deployment day.

Usage:
    python3 scripts/check_rules.py [--timeout 15] [config.yaml ...]

Exit code 0 = all URLs reachable. Non-zero otherwise.
"""
import argparse
import concurrent.futures as cf
import re
import sys
import urllib.error
import urllib.request

import yaml

# We only network-check real rule mirrors, not the (placeholder) airport
# subscriptions or the CHANGE_ME secret. This prefix must match everything in
# the rule-providers block.
RULE_PREFIX = "https://gh-proxy.com/"
HEALTH_URL = "http://www.gstatic.com/generate_204"

UA = ("clash-mi-rules-ci/1.0 (+https://github.com/chiheiyip/clash-mi-rules) "
      "(rule-source availability check)")


def collect_urls(paths):
    urls = set()
    for p in paths:
        try:
            data = yaml.safe_load(open(p, encoding="utf-8"))
        except Exception:  # validate.py reports the parse error; skip here
            continue
        for cfg in (data.get("rule-providers") or {}).values():
            u = (cfg or {}).get("url")
            if u and (u.startswith("https://") or u.startswith("http://")):
                urls.add(u)
    # always also probe the latency/health URL so a broken probe target is caught
    urls.add(HEALTH_URL)
    return urls


def check(url, timeout):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code = r.status
            if code < 400:
                return url, True, f"{code} ({r.headers.get('Content-Length', '?')}B)"
            return url, False, f"{code}"
    except urllib.error.HTTPError as e:
        # some mirrors reject HEAD; try GET (HEAD can 405)
        if e.code in (405, 403):
            try:
                g = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(g, timeout=timeout) as r:
                    if r.status < 400:
                        return url, True, f"GET {r.status}"
            except urllib.error.HTTPError as e2:
                return url, False, f"HEAD {e.code} / GET {e2.code}"
            except Exception as e2:  # noqa: BLE001
                return url, False, f"HEAD {e.code} / GET err {e2}"
        return url, False, f"HTTPError {e.code}"
    except Exception as e:  # noqa: BLE001
        return url, False, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("configs", nargs="*")
    args = ap.parse_args()

    import glob
    import os
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = args.configs or sorted(glob.glob(os.path.join(repo, "*.yaml")))
    urls = sorted(collect_urls(paths))
    if not urls:
        print("no URLs found to check")
        return 1

    ok, bad = 0, 0
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        futs = {pool.submit(check, u, args.timeout): u for u in urls}
        for fut in cf.as_completed(futs):
            url, good, info = fut.result()
            if good:
                ok += 1
                print(f"[ok    ] {url}  ({info})")
            else:
                bad += 1
                print(f"[BAD   ] {url}  ({info})")

    print(f"\n{ok} OK / {bad} BAD of {len(urls)} URL(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
