#!/bin/bash
# domino-container-lp-recipe / apply-lp.sh
#
# One-shot LP integration: clone (or use existing) upstream domino-container
# at the tested commit, reset patched files, then run patch.py for chosen
# languages.
#
# 一鍵 LP 整合：clone（或使用既有）上游 domino-container 至 tested commit，
# reset 已 patched 的檔案，再為指定語言跑 patch.py。
#
# Usage / 用法:
#   ./apply-lp.sh --lang TC                                          # default target
#   ./apply-lp.sh --lang TC --target /path/to/domino-container       # custom target
#   ./apply-lp.sh --lang TC,SC --allow-inferred                      # multi-lang, allow inferred
#   FORCE=1 ./apply-lp.sh --lang TC                                  # skip "continue?" prompts
#
# After this script:
#   1. Place LP tar(s) in /local/software/   (e.g. Domino_14.5.1_SLP_TChinese.tar)
#   2. cd <target>
#   3. ./build.sh domino 14.5.1 -restapi=1.1.7 -leap=1.1.10 -domlp=TC

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="/local/github/domino-container"
LANG_CODES=""
DOMINO_VERSION="14.5.1"
ALLOW_INFERRED=""

TESTED_COMMIT="4734801"
UPSTREAM_URL="https://github.com/HCL-TECH-SOFTWARE/domino-container.git"

# --- parse args ---
while [ $# -gt 0 ]; do
  case "$1" in
    --lang) LANG_CODES="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --domino-version) DOMINO_VERSION="$2"; shift 2 ;;
    --allow-inferred) ALLOW_INFERRED="--allow-inferred"; shift ;;
    -h|--help)
      sed -n '2,/^set -e/p' "$0" | sed 's/^# \{0,1\}//' | sed '/^set -e/d'
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

if [ -z "$LANG_CODES" ]; then
  echo "Error: --lang is required (e.g. --lang TC)"
  echo "Run with --help for usage."
  exit 2
fi

cat <<EOF
===== domino-container-lp-recipe / apply-lp.sh =====
Target:                $TARGET
Languages:             $LANG_CODES
Domino version:        $DOMINO_VERSION
Tested upstream commit: $TESTED_COMMIT

EOF

# --- Step 1: clone or verify upstream ---
if [ -d "$TARGET/.git" ]; then
  echo "[1/3] Upstream already cloned. Checking commit..."
  cd "$TARGET"
  CURRENT=$(git rev-parse --short HEAD)
  if [ "$CURRENT" != "$TESTED_COMMIT" ]; then
    echo "  ⚠️  Current HEAD ($CURRENT) ≠ tested commit ($TESTED_COMMIT)."
    echo "      Patches may not apply cleanly. See upgrade-guide.md."
    if [ "$FORCE" != "1" ]; then
      printf "  Continue anyway? [y/N] "
      read -r ANSWER
      [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ] || {
        echo
        echo "To switch to tested commit:"
        echo "  cd $TARGET && git fetch origin && git checkout $TESTED_COMMIT"
        exit 1
      }
    fi
  else
    echo "  ✓ On tested commit $TESTED_COMMIT"
  fi
else
  echo "[1/3] Cloning upstream HCL repo to $TARGET..."
  mkdir -p "$(dirname "$TARGET")"
  git clone "$UPSTREAM_URL" "$TARGET"
  cd "$TARGET"
  git checkout "$TESTED_COMMIT"
  echo "  ✓ Cloned and checked out $TESTED_COMMIT"
fi

# --- Step 2: reset patched files to vanilla ---
# This makes patch.py idempotent across re-runs / multi-lang changes.
# 還原已 patched 的檔案為 vanilla，讓 patch.py 在重跑 / 多語言切換時保持冪等。
echo
echo "[2/3] Resetting LP-affected files to vanilla (so patch.py runs on clean state)..."
cd "$TARGET"
git checkout -- \
  build.sh \
  dockerfiles/install_dir_domino/install_domino.sh \
  dockerfiles/install_dir_common/software.txt \
  software/software.txt
echo "  ✓ Reset complete"

# --- Step 3: run patch.py ---
echo
echo "[3/3] Running patch.py..."
python3 "$SCRIPT_DIR/patch.py" \
  --target "$TARGET" \
  --lang "$LANG_CODES" \
  --domino-version "$DOMINO_VERSION" \
  $ALLOW_INFERRED

# --- Done ---
cat <<EOF

═══════════════════════════════════════════════════════════════════════════════
Done. Target is ready: $TARGET
═══════════════════════════════════════════════════════════════════════════════

Next steps / 接下來:
  1. Place LP tar(s) in /local/software/
     將 LP tar 放到 /local/software/

  2. Build (one LP per build):
     Build (一次 build 一個 LP):

         cd $TARGET
         ./build.sh domino $DOMINO_VERSION -restapi=1.1.7 -leap=1.1.10 -domlp=<CODE>

  3. After build, verify:
     Build 完後驗證:

         $SCRIPT_DIR/verify.sh --lang <CODE>

⚠️  If you've already done OneTouch Setup on /local/notesdata, rebuilding
   alone won't make existing .nsf files use the new LP. See the companion SOP:
   https://github.com/bryanHsiao/domino-container-wsl2-sop  (§12.6)
EOF
