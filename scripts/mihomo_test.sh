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

# fake-ip-filter contains `geosite:cn`; provide the official database up front
# so config testing does not depend on mihomo's own DNS/bootstrap path.
if [[ -n "${GEOSITE_DAT:-}" ]]; then
  cp "$GEOSITE_DAT" "$TMP/GeoSite.dat"
else
  curl -fsSL \
    "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat" \
    -o "$TMP/GeoSite.dat"
fi
if [[ -n "${GEOIP_DAT:-}" ]]; then
  cp "$GEOIP_DAT" "$TMP/GeoIP.metadb"
else
  curl -fsSL \
    "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb" \
    -o "$TMP/GeoIP.metadb"
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
# Replace the airport-subscription placeholders with a valid HTTP provider
# URL (a reachable mihomo-provider payload), and the secret with a safe value.
txt = txt.replace("机场A订阅地址", "https://gist.githubusercontent.com/chiheiyip/clash-mi-rules/raw/provider/direct.yml")
txt = txt.replace("机场B订阅地址", "https://gist.githubusercontent.com/chiheiyip/clash-mi-rules/raw/provider/direct2.yml")
txt = txt.replace("CHANGE_ME_TO_A_LONG_RANDOM_SECRET", "ci-sanitized-secret-please-ignore")
open(out, "w", encoding="utf-8").write(txt)
PY
  ran=$((ran+1))
  echo "=== mihomo -t : $base ==="
  log="$TMP/${base}.log"
  if "$BIN" -t -d "$TMP" -f "$out" >"$log" 2>&1; then
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
