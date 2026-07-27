#!/usr/bin/env bash
#
# Rebuild the password-protected index.html from index.src.html
#
# WORKFLOW
#   1. Edit index.src.html  <-- this is the real dashboard, always edit this one
#   2. Run: ./scripts/encrypt_site.sh
#   3. Commit and push. GitHub Pages serves the encrypted index.html.
#
# The password is NOT stored in this repo. Supply it one of two ways:
#   export STATICRYPT_PASSWORD='...'   ./scripts/encrypt_site.sh
#   ./scripts/encrypt_site.sh          # prompts interactively
#
# .staticrypt.json holds only the salt. It is safe to commit and MUST stay
# committed -- changing it changes the ciphertext for the same password.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SRC="index.src.html"
OUT="index.html"
BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_DIR"' EXIT

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: $SRC not found. It is the plaintext source for the dashboard." >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "ERROR: npx not found. Install Node.js (https://nodejs.org) first." >&2
  exit 1
fi

# staticrypt names its output after the input file, so stage the source
# under the final name inside a scratch directory.
mkdir -p "$BUILD_DIR/in" "$BUILD_DIR/out"
cp "$SRC" "$BUILD_DIR/in/$OUT"

echo "Encrypting $SRC -> $OUT ..."

PW_ARGS=()
if [[ -n "${STATICRYPT_PASSWORD:-}" ]]; then
  PW_ARGS=(-p "$STATICRYPT_PASSWORD")
fi

npx --yes staticrypt@3 "$BUILD_DIR/in/$OUT" \
  "${PW_ARGS[@]}" \
  --remember false \
  --short \
  -d "$BUILD_DIR/out" \
  -c .staticrypt.json \
  --template-title "Western Canada Production Exposure" \
  --template-instructions "This dashboard is private. Enter the access password to continue." \
  --template-button "UNLOCK" \
  --template-color-primary "#1f6feb" \
  --template-color-secondary "#0d1117"

cp "$BUILD_DIR/out/$OUT" "$OUT"

echo "Done. $OUT is encrypted ($(wc -c < "$OUT") bytes)."
echo "Commit both $SRC and $OUT, then push."
