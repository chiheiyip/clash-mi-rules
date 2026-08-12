#!/usr/bin/env python3
"""clash-mi-rules Mihomo config-test harness.

The shipped configs contain deployment placeholders (`机场A订阅地址`,
`CHANGE_ME_...`) that a *real* `mihomo -t` would reject. This harness:

  1. Copies each config to a temp working dir.
  2. Substitutes the airport-subscription placeholder with a valid ephemeral
     direct-URL provider and a random safe secret, so the kernel parser can
     load the full structure.
  3. Runs `mihomo -t -f <sanitized>` and reports per-file result.

Usage:
    scripts/mihomo_test.sh [--bin /path/to/mihomo] [config.yaml ...]

Requires a `mihomo` binary (fetched by CI from GitHub Releases). If an
executable named `mihomo` is on PATH it is used; otherwise pass `--bin`.
"""
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
  if "$BIN" -t -f "$out" >/tmp/mihomo_test.out 2>&1; then
    echo "[ok    ] $base"
  else
    echo "[BAD   ] $base"
    cat /tmp/mihomo_test.out
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
