#!/usr/bin/env python3
"""clash-mi-rules validation harness.

Runs the set of deterministic checks that CI also runs:

  1. YAML syntax parse of every *.yaml at repo root.
  2. Structural consistency across the three configs
     (rule-source URL parity, dns-recursion guard, no-interface-binding guard,
      secret / placeholder guard).
  3. Three-config parity: the two OpenClash configs must match
     clash-mi-detail.yaml rule-by-rule and group-by-group, except for the
     documented differences (IPv6, DNS fallback, find-process-mode, listeners).
  4. URLs are validated separately by `check_rules.py` (network) — this file
     is offline-only and never touches the network.

Usage:
    python3 scripts/validate.py [config.yaml ...]
    (default: all *.yaml at repo root)

Exit code 0 = all checks pass. Non-zero = at least one check failed.
"""
import argparse
import copy
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

EXPECTED_CONFIGS = {
    "clash-mi-detail.yaml",
    "openclash.yaml",
    "openclash-backnode.yaml",
}

# DNS may NOT contain a dynamically-obtained upstream (would create a loop).
FORBIDDEN_DNS_TOKENS = ("dhcp://", "system", "apclix0")

# Real (non-placeholder) rule-source URL prefixes we expect under rule-providers.
RULE_URL_PREFIXES = (
    "https://gh-proxy.com/",
    "https://ghproxy.",
)

# placeholder markers that must be replaced before real deployment
# (the CHANGE_ME_ secret has its own, more specific warning below)
PLACEHOLDER_MARKERS = ("机场A订阅地址", "机场B订阅地址", "YOUR_VLESS_UUID_PLACEHOLDER")

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

# --- three-config parity ----------------------------------------------------
# The OpenClash configs are hand-maintained copies of clash-mi-detail.yaml.
# Everything must match the general config except the documented differences
# below; anything else is drift (an edit applied to one file but not the others).
REFERENCE_CONFIG = "clash-mi-detail.yaml"
ROUTER_CONFIGS = ("openclash.yaml", "openclash-backnode.yaml")
# top-level / dns keys that may legitimately differ between the configs
PARITY_SKIP_TOP = {"ipv6", "find-process-mode", "listeners"}
PARITY_SKIP_DNS = {"ipv6", "fallback", "fallback-filter"}
# IPv6 private-range direct rules exist only where IPv6 is enabled
IPV6_PRIVATE_RULES = {
    "IP-CIDR6,::1/128,直连,no-resolve",
    "IP-CIDR6,fc00::/7,直连,no-resolve",
    "IP-CIDR6,fe80::/10,直连,no-resolve",
}

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
    if os.path.basename(path) in {"openclash.yaml", "openclash-backnode.yaml"}:
        if not raw.startswith("mode: rule\n"):
            err(f"{path}: start the file with 'mode: rule' for the OpenClash upload preview")
    live = "\n".join(
        ln for ln in raw.splitlines() if not ln.lstrip().startswith("#")
    )

    # --- deployment placeholders (expected in the template, must be replaced on deploy) ---
    present = [m for m in PLACEHOLDER_MARKERS if m in live]
    if present:
        warn(f"{path}: deployment placeholders still present (fill in before use): {present}")

    # --- VLESS listener users ---
    for lst in data.get("listeners") or []:
        for user in (lst or {}).get("users") or []:
            uuid = str((user or {}).get("uuid", ""))
            if uuid != "YOUR_VLESS_UUID_PLACEHOLDER" and not UUID_RE.match(uuid):
                warn(f"{path}: listener {lst.get('name')!r} uuid is not a standard UUID: {uuid!r}")

    for m in re.finditer(r"([\w./-]+)#(apcli\w+|eth\w+|wwan\w+|pppoe\w+|usb\w+)", live):
        err(f"{path}: hard-coded interface binding found in live config (breaks portability): {m.group(0)}")

    # --- rule-provider sanity ---
    rp = data.get("rule-providers") or {}
    for name, cfg in rp.items():
        cfg = cfg or {}
        provider_type = cfg.get("type")
        if provider_type == "http":
            url = cfg.get("url")
            if not url:
                err(f"{path}: HTTP rule-provider {name!r} has no url")
                continue
            if not url.startswith(RULE_URL_PREFIXES):
                warn(f"{path}: rule-provider {name!r} url does not match known mirror prefix: {url}")
        elif provider_type == "inline":
            if not cfg.get("payload"):
                err(f"{path}: inline rule-provider {name!r} has an empty payload")
        else:
            err(f"{path}: rule-provider {name!r} has unsupported/missing type: {provider_type!r}")

    # --- every RULE-SET reference must resolve to a provider ---
    for rule in data.get("rules") or []:
        if not isinstance(rule, str) or not rule.startswith("RULE-SET,"):
            continue
        provider = rule.split(",", 2)[1]
        if provider not in rp:
            err(f"{path}: rule references missing rule-provider {provider!r}: {rule}")


def check_consistency(paths, loaded):
    """Cross-config checks: rule-source parity should be close.

    We don't require byte-identical rule sets (detail vs openclash differ by
    ipv6 + tls fallback), but every rule-provider URL referenced in *any*
    config must resolve to a prefix we recognize, and the three configs must
    not drift on the DNS recursion / placeholder rules.
    """
    if len(paths) < 2:
        return
    # Every config must reference exactly the same external rule-source pool.
    url_sets = {}
    for p, data in loaded.items():
        url_sets[p] = {
            (cfg or {}).get("url")
            for cfg in (data.get("rule-providers") or {}).values()
            if (cfg or {}).get("type") == "http" and (cfg or {}).get("url")
        }
    if url_sets:
        reference_path, reference_urls = next(iter(url_sets.items()))
        for p, urls in url_sets.items():
            if urls != reference_urls:
                err(f"{p}: external rule-source pool differs from {reference_path}")


def _normalize(data):
    """Drop the documented per-config differences so the rest can be compared."""
    d = copy.deepcopy(data)
    for k in PARITY_SKIP_TOP:
        d.pop(k, None)
    dns = d.get("dns")
    if isinstance(dns, dict):
        for k in PARITY_SKIP_DNS:
            dns.pop(k, None)
    d["rules"] = [r for r in d.get("rules") or [] if r not in IPV6_PRIVATE_RULES]
    return d


def _first_rule_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return f"rule #{i + 1}: {x!r} != {y!r}"
    return f"rule count {len(a)} != {len(b)}"


def check_parity(loaded):
    """Rule-by-rule / group-by-group parity of the router configs vs the general one."""
    by_name = {os.path.basename(p): (p, d) for p, d in loaded.items()}
    if REFERENCE_CONFIG not in by_name:
        return
    _, ref = by_name[REFERENCE_CONFIG]
    ref_n = _normalize(ref)
    for name in ROUTER_CONFIGS:
        if name not in by_name:
            continue
        path, data = by_name[name]

        # the documented differences must actually hold
        if data.get("ipv6") is not False or (data.get("dns") or {}).get("ipv6") is not False:
            err(f"{path}: router configs must set top-level ipv6 and dns.ipv6 to false")
        fpm = data.get("find-process-mode")
        if fpm != "off":
            # YAML 1.1 parsers (incl. OpenClash's Ruby tooling) read a bare `off` as false
            err(f"{path}: find-process-mode must be the quoted string \"off\" (got {fpm!r})")
        has_listeners = "listeners" in data
        if has_listeners != (name == "openclash-backnode.yaml"):
            err(f"{path}: listeners block belongs only in openclash-backnode.yaml")

        # everything else must match the general config
        cur_n = _normalize(data)
        for key in sorted(set(ref_n) | set(cur_n)):
            a, b = ref_n.get(key), cur_n.get(key)
            if a == b:
                continue
            if key == "rules" and isinstance(a, list) and isinstance(b, list):
                detail = _first_rule_diff(a, b)
            else:
                detail = "values differ"
            err(f"{path}: drift from {REFERENCE_CONFIG} in {key!r} ({detail})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("configs", nargs="*")
    args = ap.parse_args()
    paths = args.configs or sorted(glob.glob(os.path.join(REPO, "*.yaml")))
    if not paths:
        err("no *.yaml found at repo root")
    loaded = {}
    for p in paths:
        check_yaml(p)
        data = load(p)
        if data:
            loaded[p] = data

    if not args.configs:
        actual = {os.path.basename(p) for p in paths}
        missing = EXPECTED_CONFIGS - actual
        if missing:
            err(f"repository is missing expected config(s): {sorted(missing)}")
    check_consistency(paths, loaded)
    check_parity(loaded)

    for w in warnings:
        print(f"[warn ] {w}")
    for e in errors:
        print(f"[error] {e}")

    print(f"\n{len(paths)} config(s) checked. "
          f"{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
