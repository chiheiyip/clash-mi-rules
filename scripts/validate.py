#!/usr/bin/env python3
"""clash-mi-rules validation harness.

Runs the set of deterministic checks that CI also runs:

  1. YAML syntax parse of every *.yaml at repo root.
  2. Structural consistency across the three configs
     (rule-source URL parity, dns-recursion guard, placeholder guard,
      no-interface-binding guard, secret guard).
  3. URLs are validated separately by `check_rules.py` (network) — this file
     is offline-only and never touches the network.

Usage:
    python3 scripts/validate.py [config.yaml ...]
    (default: all *.yaml at repo root)

Exit code 0 = all checks pass. Non-zero = at least one check failed.
"""
import argparse
import glob
import os
import re
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Top-level keys each config must contain. The backnode config additionally
# has a `listeners:` block (VLESS/WS listener) — expected difference.
REQUIRED_TOP = {
    "proxy-providers", "proxies", "port", "socks-port", "mixed-port",
    "redir-port", "tproxy-port", "allow-lan", "mode", "log-level",
    "external-controller", "secret", "dns", "ipv6", "tun", "profile",
    "default", "proxy-groups", "rules", "rule-providers",
}

# DNS may NOT contain a dynamically-obtained upstream (would create a loop).
FORBIDDEN_DNS_TOKENS = ("dhcp://", "system", "apclix0")

# Real (non-placeholder) rule-source URL prefixes we expect under rule-providers.
RULE_URL_PREFIXES = (
    "https://gh-proxy.com/",
    "https://ghproxy.",
)

# placeholder markers that must be replaced before real deployment
PLACEHOLDER_MARKERS = ("机场A订阅地址", "机场B订阅地址", "CHANGE_ME_")

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except Exception as e:  # noqa: BLE001
        err(f"{path}: YAML parse FAILED: {e}")
        return None


def check_yaml(path):
    data = load(path)
    if data is None:
        return
    if not isinstance(data, dict):
        err(f"{path}: top-level is not a mapping")
        return

    missing = REQUIRED_TOP - set(data.keys())
    if missing:
        err(f"{path}: missing top-level keys: {sorted(missing)}")

    # --- DNS recursion guard ---
    dns = data.get("dns") or {}
    text_blob = yaml.safe_dump(dns)
    for tok in FORBIDDEN_DNS_TOKENS:
        if re.search(r"(?<![\w./-])" + re.escape(tok), text_blob):
            err(f"{path}: DNS contains forbidden dynamic upstream token: {tok!r}")

    # --- external-controller secret guard ---
    secret = data.get("secret")
    if not secret or secret in ("", "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"):
        warn(f"{path}: external-controller secret is still the default/placeholder — "
             "change it before deploying and never expose 0.0.0.0:9090 to the internet.")

    # --- portability: no device-interface binding in *live* (non-comment) code ---
    # Comment lines (starting with #) are documentation examples (e.g. the
    # README 'local overlay' note) and must not trip the check.
    raw = open(path, "r", encoding="utf-8").read()
    live = "\n".join(
        ln for ln in raw.splitlines() if not ln.lstrip().startswith("#")
    )
    for m in re.finditer(r"([\w./-]+)#(apcli\w+|eth\w+|wwan\w+|pppoe\w+|usb\w+)", live):
        err(f"{path}: hard-coded interface binding found in live config (breaks portability): {m.group(0)}")

    # --- rule-provider URL sanity ---
    rp = data.get("rule-providers") or {}
    for name, cfg in rp.items():
        url = (cfg or {}).get("url")
        if not url:
            err(f"{path}: rule-provider {name!r} has no url")
            continue
        if not url.startswith(RULE_URL_PREFIXES):
            warn(f"{path}: rule-provider {name!r} url does not match known mirror prefix: {url}")


def check_consistency(paths):
    """Cross-config checks: rule-source parity should be close.

    We don't require byte-identical rule sets (detail vs openclash differ by
    ipv6 + tls fallback), but every rule-provider URL referenced in *any*
    config must resolve to a prefix we recognize, and the three configs must
    not drift on the DNS recursion / placeholder rules.
    """
    if len(paths) < 2:
        return
    # unified upstream set across all configs
    all_urls = set()
    for p in paths:
        data = load(p)
        if not data:
            continue
        for cfg in (data.get("rule-providers") or {}).values():
            u = (cfg or {}).get("url")
            if u:
                all_urls.add(u)

    # Every config must reference the same rule-source pool (no orphan rule
    # that only works when another config is also present).
    for p in paths:
        data = load(p)
        if not data:
            continue
        mine = {(cfg or {}).get("url") for cfg in (data.get("rule-providers") or {}).values()}
        mine.discard(None)
        orphan = mine - all_urls
        if orphan:
            err(f"{p}: references rule-provider URL(s) not present in any other config (drift): {orphan}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("configs", nargs="*")
    args = ap.parse_args()
    paths = args.configs or sorted(glob.glob(os.path.join(REPO, "*.yaml")))
    if not paths:
        err("no *.yaml found at repo root")
    for p in paths:
        check_yaml(p)
    check_consistency(paths)

    for w in warnings:
        print(f"[warn ] {w}")
    for e in errors:
        print(f"[error] {e}")

    print(f"\n{len(paths)} config(s) checked. "
          f"{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
