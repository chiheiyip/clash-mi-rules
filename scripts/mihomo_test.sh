#!/usr/bin/env bash
# clash-mi-rules Mihomo config-test harness.
#
# The shipped configs contain deployment placeholders (airport URLs and the
# controller secret) that a real `mihomo -t` would reject. This harness copies
# each config, replaces those placeholders, and tests the sanitized copy.
#
# Usage:
#   scripts/mihomo_test.sh [--bin /path/to/mihomo] [config.yaml ...]
#
# Requires a mihomo binary. CI fetches one from the official GitHub release;
# locally, put `mihomo` on PATH or pass --bin.
set -euo pipefail

BIN="${MIHOMO_BIN:-}"
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bin) BIN="$2"; shift 2 ;;
    *) EXTRA+=("$1") ;; # config file paths
  esac
done

if [[ -z "$BIN" ]]; then
  BIN="$(command -v mihomo 2>/dev/null || true)"
fi
if [[ -z "$BIN" ]]; then
  echo "ERROR: no mihomo binary found (set MIHOMO_BIN or --bin)" >&2
  echo "TIP:  fetch one, e.g.:  --bin ./bin/mihomo  (or add mihomo to PATH)" >&2
  exit 2
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
shopt -s nullglob
if [[ ${#EXTRA[@]} -eq 0 ]]; then
  EXTRA=("$REPO"/*.yaml)
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# GEO databases: each config runs in its own empty home directory, and the
# sanitized copy points geox-url at an unreachable address. A config that
# silently needs a database it was not given therefore FAILS instead of
# downloading it. Only configs that use GeoIP (dns.fallback-filter.geoip)
# receive the GeoIP mmdb; the OpenClash configs must start with none at all.
GEOIP_SRC="$TMP/GeoIP.metadb.src"
if [[ -n "${GEOIP_DAT:-}" ]]; then
  cp "$GEOIP_DAT" "$GEOIP_SRC"
else
  curl -fsSL \
    "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb" \
    -o "$GEOIP_SRC"
fi

fail=0
ran=0
for src in "${EXTRA[@]}"; do
  [[ -f "$src" ]] || { echo "[skip ] missing: $src"; continue; }
  base="$(basename "$src")"
  out="$TMP/$base"
  python3 - "$src" "$out" <<'PY'
import sys
src, out = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8").read()
# Replace the airport-subscription placeholders with syntactically valid URLs
# and the secret with a safe value. `mihomo -t` validates the config only; it
# does not depend on the subscription content, so the URLs need not resolve.
txt = txt.replace("机场A订阅地址", "https://example.com/clash-mi-rules-ci/sub-a.yaml")
txt = txt.replace("机场B订阅地址", "https://example.com/clash-mi-rules-ci/sub-b.yaml")
txt = txt.replace("CHANGE_ME_TO_A_LONG_RANDOM_SECRET", "ci-sanitized-secret-please-ignore")
# Any GEO download attempt must fail fast (see the note above).
txt = txt.replace("https://gh-proxy.com/github.com/MetaCubeX/meta-rules-dat/releases/download/latest/",
                  "http://127.0.0.1:9/geo-download-blocked-in-test/")
open(out, "w", encoding="utf-8").write(txt)
PY
  home="$TMP/home-$base"
  mkdir -p "$home"
  needs_geoip="$(python3 -c 'import sys,yaml; d=yaml.safe_load(open(sys.argv[1],encoding="utf-8")); print("yes" if ((d.get("dns") or {}).get("fallback-filter") or {}).get("geoip") else "no")' "$out")"
  if [[ "$needs_geoip" == "yes" ]]; then
    cp "$GEOIP_SRC" "$home/GeoIP.metadb"
  fi
  echo "[geo   ] $base: GeoIP mmdb provided=$needs_geoip, everything else absent"
  ran=$((ran+1))
  echo "=== mihomo -t : $base ==="
  log="$TMP/${base}.log"
  if "$BIN" -t -d "$home" -f "$out" >"$log" 2>&1; then
    echo "[ok    ] $base"
  else
    echo "[BAD   ] $base"
    cat "$log"
    fail=1
  fi
done

if [[ $ran -eq 0 ]]; then
  echo "no config files tested"
  exit 2
fi
echo
if [[ $fail -eq 0 ]]; then
  echo "mihomo -t: ALL PASSED ($ran)"
else
  echo "mihomo -t: FAILED (see above)"
fi
exit $fail
