#!/bin/bash
# domino-container-lp-recipe / verify.sh
#
# Run AFTER ./build.sh ... -domlp=<CODE> completes.
# Three independent checks per language.
#
# 在 build 完成後跑，對指定語言做三項獨立驗證。
#
# Usage / 用法:
#   ./verify.sh --lang TC                                     # default image hclcom/domino:14.5.1
#   ./verify.sh --lang TC --image hclcom/domino:14.5.1
#   ./verify.sh --lang TC --container domino-lab              # also check runtime console.log

LANG_CODE=""
IMAGE="hclcom/domino:14.5.1"
CONTAINER=""

while [ $# -gt 0 ]; do
  case "$1" in
    --lang) LANG_CODE="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --container) CONTAINER="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --lang <CODE> [--image <image>] [--container <name>]"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

if [ -z "$LANG_CODE" ]; then
  echo "Error: --lang is required (e.g. --lang TC)"
  exit 2
fi

LANG_LCASE=$(echo "$LANG_CODE" | tr '[:upper:]' '[:lower:]')

echo "===== Verify Language Pack integration ====="
echo "Language: $LANG_CODE"
echo "Image:    $IMAGE"
echo

# --- Check 1: image label ---
echo "[1/3] Image label DominoContainer.addons should include languagepack=$LANG_CODE"
ADDONS=$(docker image inspect "$IMAGE" --format '{{ index .Config.Labels "DominoContainer.addons" }}' 2>/dev/null)
if [ -z "$ADDONS" ]; then
  echo "  ❌ Image $IMAGE not found. Build it first."
elif echo "$ADDONS" | grep -q "languagepack=$LANG_CODE"; then
  echo "  ✓ $ADDONS"
else
  echo "  ❌ $LANG_CODE not in addons label: $ADDONS"
fi
echo

# --- Check 2: language resources in image ---
# Map LANG_CODE to a directory keyword to search.
# For most languages: try lowercase code AND installer code variants.
echo "[2/3] Image contains $LANG_CODE/$LANG_LCASE resource directories"
COUNT=$(docker run --rm --entrypoint /bin/bash "$IMAGE" -c \
  "find / -iname '*$LANG_LCASE*' 2>/dev/null | wc -l" 2>/dev/null)
if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
  echo "  ✓ Found $COUNT path(s) matching '$LANG_LCASE'"
else
  echo "  ⚠️  No paths matching '$LANG_LCASE' found (might use installer_code instead — check manually)"
fi
echo

# --- Check 3: LP install log message ---
echo "[3/3] LP install log records successful install"
docker run --rm --entrypoint /bin/bash "$IMAGE" -c \
  'grep -i "Selected Language Packs" /tmp/domino-container/install_domlp.log 2>/dev/null' \
  | head -1 | sed 's/^/  /'

# --- Check 4 (optional): runtime console.log ---
if [ -n "$CONTAINER" ]; then
  echo
  echo "[4/3, runtime] Container $CONTAINER console.log should contain target-language strings"
  if docker ps --filter "name=$CONTAINER" --format '{{.Names}}' 2>/dev/null | grep -q "$CONTAINER"; then
    # Heuristic: look for non-ASCII bytes (any language); user has to interpret
    HITS=$(docker exec "$CONTAINER" sh -c \
      "grep -ac '[^[:print:][:space:]]' /local/notesdata/IBM_TECHNICAL_SUPPORT/console.log 2>/dev/null" \
      || echo "0")
    if [ "$HITS" != "0" ]; then
      echo "  ✓ Console.log contains $HITS non-ASCII line(s). Sample:"
      docker exec "$CONTAINER" sh -c \
        "grep -a '[^[:print:][:space:]]' /local/notesdata/IBM_TECHNICAL_SUPPORT/console.log 2>/dev/null | head -3" \
        | sed 's/^/    /'
    else
      echo "  ⚠️  No non-ASCII strings in console.log. Possible causes:"
      echo "       - /local/notesdata was reused from a pre-LP setup ('Data already installed' skip)"
      echo "       - Server hasn't done much localized logging yet"
      echo "      See docs/sync-trap-caveat.md."
    fi
  else
    echo "  (skipped — container $CONTAINER not running)"
  fi
fi
