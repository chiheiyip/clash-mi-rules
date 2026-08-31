#!/usr/bin/env python3
"""clash-mi-rules validation harness.

Runs the set of deterministic checks that CI also runs:

  1. YAML syntax parse of every *.yaml at repo root.
  2. Structural consistency across the five configs
     (rule-source URL parity, dns-recursion guard, no-interface-binding guard,
      secret guard, plus SSLVPN derivation and campus-rule priority checks).
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

EXPECTED_CONFIGS = {
    "clash-mi-detail.yaml",
    "clash-mi-detail-sslvpn.yaml",
    "openclash.yaml",
    "openclash-sslvpn.yaml",
    "openclash-backnode.yaml",
}

SSLVPN_DERIVATIVES = {
    "clash-mi-detail-sslvpn.yaml": "clash-mi-detail.yaml",
    "openclash-sslvpn.yaml": "openclash.yaml",
}

EASYCONNECT_NODE = "SCUT-EasyConnect"
CAMPUS_GROUP = "校园网"
CAMPUS_FALLBACK_GROUP = "校园网-故转"
CAMPUS_PROVIDER = "SCUT Campus"
CAMPUS_RULE = f"RULE-SET,{CAMPUS_PROVIDER},{CAMPUS_GROUP}"
VPN_DIRECT_RULES = (
    "DOMAIN,sslvpn2.scut.edu.cn,直连",
    "DOMAIN,sslvpn3.scut.edu.cn,直连",
    "DOMAIN,webvpn.scut.edu.cn,直连",
)
PORTAL_DIRECT_RULES = (
    "DOMAIN,s.scut.edu.cn,直连",
    "IP-CIDR,202.38.210.131/32,直连,no-resolve",
)
VPN_FAKE_IP_FILTER = (
    "sslvpn2.scut.edu.cn",
    "sslvpn3.scut.edu.cn",
    "webvpn.scut.edu.cn",
)

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


def _named(items):
    return {item.get("name"): item for item in items if isinstance(item, dict) and item.get("name")}


def _normalise_sslvpn(data):
    """Remove the deliberately-added SSLVPN overlay and return the base shape."""
    import copy
    data = copy.deepcopy(data)
    data["proxies"] = [p for p in data.get("proxies", []) if p.get("name") != EASYCONNECT_NODE]
    groups = []
    for group in data.get("proxy-groups", []):
        if group.get("name") in (CAMPUS_GROUP, CAMPUS_FALLBACK_GROUP):
            continue
        if isinstance(group.get("filter"), str):
            group["filter"] = group["filter"].replace("(SCUT-EasyConnect|", "(")
        groups.append(group)
    data["proxy-groups"] = groups
    data["rules"] = [
        rule for rule in data.get("rules", [])
        if rule != CAMPUS_RULE and rule not in VPN_DIRECT_RULES
    ]
    data.get("rule-providers", {}).pop(CAMPUS_PROVIDER, None)
    fake_filter = (data.get("dns") or {}).get("fake-ip-filter") or []
    data["dns"]["fake-ip-filter"] = [x for x in fake_filter if x not in VPN_FAKE_IP_FILTER]
    return data


def check_sslvpn(path, data, base_path, base):
    """Validate EasyConnect wiring and prove the SSLVPN file is only an overlay."""
    nodes = _named(data.get("proxies") or [])
    node = nodes.get(EASYCONNECT_NODE)
    expected_node = {
        "name": EASYCONNECT_NODE,
        "type": "socks5",
        "server": "127.0.0.1",
        "port": 1080,
        "udp": False,
    }
    if node != expected_node:
        err(f"{path}: {EASYCONNECT_NODE} must be the local SOCKS5 node {expected_node}")

    groups = _named(data.get("proxy-groups") or [])
    campus = groups.get(CAMPUS_GROUP) or {}
    fallback = groups.get(CAMPUS_FALLBACK_GROUP) or {}
    if campus.get("type") != "select" or campus.get("proxies") != [
            CAMPUS_FALLBACK_GROUP, EASYCONNECT_NODE, "直连"]:
        err(f"{path}: {CAMPUS_GROUP} must offer auto fallback, EasyConnect and direct in that order")
    if fallback.get("type") != "fallback" or fallback.get("proxies") != [EASYCONNECT_NODE, "直连"]:
        err(f"{path}: {CAMPUS_FALLBACK_GROUP} must fall back from EasyConnect to direct")

    # Prevent the local EasyConnect node from leaking into global/other groups
    # through include-all. Regional positive-match filters do not match its name.
    for name in ("所有-手动", "所有-自动", "其他-手动", "其他-自动"):
        if EASYCONNECT_NODE not in (groups.get(name) or {}).get("filter", ""):
            err(f"{path}: group {name!r} does not exclude {EASYCONNECT_NODE}")

    provider = (data.get("rule-providers") or {}).get(CAMPUS_PROVIDER) or {}
    payload = provider.get("payload") or []
    if provider.get("type") != "inline" or provider.get("behavior") != "classical":
        err(f"{path}: {CAMPUS_PROVIDER!r} must be an inline classical rule-provider")
    if not any(str(x).startswith("DOMAIN") for x in payload):
        err(f"{path}: {CAMPUS_PROVIDER!r} must contain campus/library domains")
    if not any(str(x).startswith("IP-CIDR") for x in payload):
        err(f"{path}: {CAMPUS_PROVIDER!r} must contain campus server IP rules")
    forbidden_payload = ("s.scut.edu.cn", "sslvpn2.scut.edu.cn", "sslvpn3.scut.edu.cn", "webvpn.scut.edu.cn")
    for entry in payload:
        if any(domain in str(entry) for domain in forbidden_payload):
            err(f"{path}: control-plane/Portal entry must stay DIRECT, not in campus payload: {entry}")

    rules = data.get("rules") or []
    if CAMPUS_RULE not in rules:
        err(f"{path}: missing campus RULE-SET reference: {CAMPUS_RULE}")
    else:
        campus_i = rules.index(CAMPUS_RULE)
        for direct_rule in (*PORTAL_DIRECT_RULES, *VPN_DIRECT_RULES):
            if direct_rule not in rules or rules.index(direct_rule) > campus_i:
                err(f"{path}: highest-priority DIRECT rule must precede campus rule: {direct_rule}")
        for lower_rule in ("RULE-SET,ChatGPT / Domain,ChatGPT", "RULE-SET,Proxy / Domain,国外", "MATCH,其他"):
            if lower_rule not in rules or rules.index(lower_rule) < campus_i:
                err(f"{path}: campus rule must precede normal split/fallback rule: {lower_rule}")

    fake_filter = (data.get("dns") or {}).get("fake-ip-filter") or []
    for domain in ("s.scut.edu.cn", *VPN_FAKE_IP_FILTER):
        if domain not in fake_filter:
            err(f"{path}: fake-ip-filter missing Portal/VPN control-plane domain: {domain}")

    if _normalise_sslvpn(data) != base:
        err(f"{path}: drifted from {base_path}; only the validated EasyConnect/campus overlay may differ")


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

    by_basename = {os.path.basename(p): (p, data) for p, data in loaded.items()}
    for child_name, base_name in SSLVPN_DERIVATIVES.items():
        if child_name in by_basename and base_name in by_basename:
            child_path, child = by_basename[child_name]
            base_path, base = by_basename[base_name]
            check_sslvpn(child_path, child, base_path, base)

    # Baseline configs must remain free of the optional EasyConnect overlay.
    for name, (p, data) in by_basename.items():
        if name in SSLVPN_DERIVATIVES:
            continue
        if EASYCONNECT_NODE in _named(data.get("proxies") or []):
            err(f"{p}: optional EasyConnect node leaked into a baseline config")
        if CAMPUS_PROVIDER in (data.get("rule-providers") or {}):
            err(f"{p}: optional campus provider leaked into a baseline config")


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

    for w in warnings:
        print(f"[warn ] {w}")
    for e in errors:
        print(f"[error] {e}")

    print(f"\n{len(paths)} config(s) checked. "
          f"{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
