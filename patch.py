#!/usr/bin/env python3
"""
domino-container-lp-recipe / patch.py

Applies Language Pack integration patches to an upstream
HCL-TECH-SOFTWARE/domino-container clone, for one or more languages
defined in language_registry.py.

Three patch targets per language:
  1. build.sh                                     — 4 edits to add the language
                                                    to the LP menu
  2. dockerfiles/install_dir_domino/install_domino.sh
                                                  — case mapping line for LNXDomLP
  3. software/software.txt
     + dockerfiles/install_dir_common/software.txt
                                                  — manifest entry in both files

Idempotent against vanilla upstream: re-running with the same --lang set
produces the same result. For incremental additions (TC already applied,
adding KO), run apply-lp.sh which resets the patched files first.

Usage:
    python3 patch.py --target /path/to/domino-container --lang TC
    python3 patch.py --target /path/to/domino-container --lang TC,SC

繁體：對上游 domino-container clone 套用一個或多個語言（在 language_registry.py
定義）的 Language Pack 整合 patch。
每個語言會 patch 三處：build.sh / install_domino.sh / 兩份 software.txt。
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

# import the registry from a sibling file
sys.path.insert(0, str(Path(__file__).resolve().parent))
import language_registry as registry

TESTED_COMMIT = "4734801"


def backup(path: Path) -> Path:
    bak = path.with_suffix(path.suffix + f".bak.{int(time.time())}")
    shutil.copy(path, bak)
    return bak


def fail(msg: str) -> None:
    print(f"\n❌ {msg}", file=sys.stderr)
    print(f"\nRecipe is tested against upstream commit {TESTED_COMMIT}.", file=sys.stderr)
    print("If upstream differs, see upgrade-guide.md.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# build.sh patches — anchored to "JA" (the last upstream-supported language)
# ---------------------------------------------------------------------------
# Strategy: always patch on top of vanilla upstream (apply-lp.sh handles
# `git checkout --` before invoking). This keeps anchors simple and stable.
# All new languages get inserted between JA and the next case (`*)` or `esac`),
# so order across multiple --lang values is preserved by sorted iteration.

def patch_buildsh(target: Path, langs: list[tuple[str, dict]]) -> None:
    f = target / "build.sh"
    print(f"[1/3] build.sh — {f}")

    if not f.is_file():
        fail(f"build.sh not found at {f}")

    content = f.read_text(encoding="utf-8")
    backup(f)

    # Each new language adds 4 things; we build the insertions cumulatively
    # by repeatedly anchoring to JA / *) / esac.
    for code, cfg in langs:
        display = cfg["display_name"]
        keypress = cfg["keypress"]

        # --- P1: LP_<CODE> variable in two functions (after LP_JA="Japanese") ---
        old1 = '  local LP_JA="Japanese"\n'
        new1 = f'  local LP_JA="Japanese"\n  local LP_{code}="{display}"\n'
        cnt = content.count(old1)
        if cnt != 2:
            fail(f"[{code}] P1: expected 2 LP_JA matches, found {cnt}")
        content = content.replace(old1, new1)

        # --- P2: <CODE>) case in get_language_pack_display_name ---
        old2 = '    JA)\n      DISPLAY_DOMLP="$LP_JA"\n      ;;\n\n    *)'
        new2 = (
            '    JA)\n      DISPLAY_DOMLP="$LP_JA"\n      ;;\n\n'
            f'    {code})\n      DISPLAY_DOMLP="$LP_{code}"\n      ;;\n\n'
            '    *)'
        )
        cnt = content.count(old2)
        if cnt != 1:
            fail(f"[{code}] P2: expected 1 'JA → *)' block, found {cnt}")
        content = content.replace(old2, new2)

        # --- P3: print_lp "<CODE>" line in select_language_pack ---
        old3 = '  print_lp "JA" "$LP_JA"\n'
        new3 = f'  print_lp "JA" "$LP_JA"\n  print_lp "{code}" "$LP_{code}"\n'
        cnt = content.count(old3)
        if cnt != 1:
            fail(f"[{code}] P3: expected 1 print_lp JA line, found {cnt}")
        content = content.replace(old3, new3)

        # --- P4: <keypress>) keypress case in select_language_pack ---
        old4 = (
            '    j)\n      SELECT_DOMLP_LANG=JA\n      DISPLAY_DOMLP="$LP_JA"\n      ;;\n\n  esac'
        )
        new4 = (
            '    j)\n      SELECT_DOMLP_LANG=JA\n      DISPLAY_DOMLP="$LP_JA"\n      ;;\n\n'
            f'    {keypress})\n      SELECT_DOMLP_LANG={code}\n      DISPLAY_DOMLP="$LP_{code}"\n      ;;\n\n'
            '  esac'
        )
        cnt = content.count(old4)
        if cnt != 1:
            fail(f"[{code}] P4: expected 1 'j) → esac' block, found {cnt}")
        content = content.replace(old4, new4)

        print(f"  ✓ {code} ({display}, keypress='{keypress}') — 4 edits applied")

    f.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# install_domino.sh patch — single case mapping for non-ISO short codes
# ---------------------------------------------------------------------------

def patch_install_domino(target: Path, langs: list[tuple[str, dict]]) -> None:
    f = target / "dockerfiles" / "install_dir_domino" / "install_domino.sh"
    print(f"\n[2/3] install_domino.sh — {f}")

    if not f.is_file():
        fail(f"install_domino.sh not found at {f}")

    content = f.read_text(encoding="utf-8")
    backup(f)

    # Build case statement from registered languages whose ISO-639-1 short code
    # doesn't match the installer code (i.e. needs mapping).
    case_lines = []
    for code, cfg in langs:
        if cfg["installer_code"] is None:
            fail(
                f"[{code}] installer_code is None (status='template'). "
                f"Fill it in language_registry.py first. "
                f"See docs/adding-new-language.md."
            )
        lcase = code.lower()
        installer = cfg["installer_code"]
        # Only emit a case if mapping is non-trivial
        # (i.e. lowercased short code != installer code).
        # For DE/JA/etc this would be a no-op, but those don't go through this recipe.
        if lcase != installer:
            case_lines.append(f"      {lcase}) DOMLP_LANG_LCASE={installer} ;;")

    if not case_lines:
        print("  ↳ No mappings needed for the chosen languages (installer codes match lowercased short codes)")
        return

    old = (
        '    local DOMINO_LP_INI="$(pwd)/domlp.ini"\n'
        '    local DOMLP_LANG_LCASE=$(echo "$DOMLP_VER" | cut -d"-" -f1 | awk \'{print tolower($0)}\')\n'
        '\n'
        '    echo "[Notes]" > "$DOMINO_LP_INI"'
    )

    case_block = "\n".join(case_lines)
    new = (
        '    local DOMINO_LP_INI="$(pwd)/domlp.ini"\n'
        '    local DOMLP_LANG_LCASE=$(echo "$DOMLP_VER" | cut -d"-" -f1 | awk \'{print tolower($0)}\')\n'
        '\n'
        '    # Map non-ISO short codes to the values LNXDomLP expects internally.\n'
        '    # Verified by: strings LNXDomLP | grep LangCodeList\n'
        '    case "$DOMLP_LANG_LCASE" in\n'
        f'{case_block}\n'
        '    esac\n'
        '\n'
        '    echo "[Notes]" > "$DOMINO_LP_INI"'
    )

    if content.count(old) != 1:
        fail("install_domino.sh anchor (DOMLP_LANG_LCASE assignment) not found. Upstream may have changed.")

    content = content.replace(old, new)
    f.write_text(content, encoding="utf-8")
    for line in case_lines:
        print(f"  ✓ {line.strip()}")


# ---------------------------------------------------------------------------
# software.txt patches — manifest entry in both files
# ---------------------------------------------------------------------------

def patch_software_txt(target: Path, langs: list[tuple[str, dict]], domino_version: str) -> None:
    print(f"\n[3/3] software.txt — appending entries for Domino {domino_version}")

    files = [
        target / "software" / "software.txt",
        target / "dockerfiles" / "install_dir_common" / "software.txt",
    ]
    for f in files:
        if not f.is_file():
            fail(f"{f.relative_to(target)} not found")

    new_entries = []
    for code, cfg in langs:
        entries = cfg.get("manifest_entries", {})
        if domino_version not in entries:
            print(
                f"  ⚠️  [{code}] no manifest entry for Domino {domino_version} in registry; "
                f"skipping software.txt update for this language."
            )
            continue
        e = entries[domino_version]
        line = f"domlp|{code}-{domino_version}|{e['tar']}|{e['hcl_id']}|{e['sha256']}"
        new_entries.append((code, line))

    if not new_entries:
        print(f"  ↳ No manifest entries to add for Domino {domino_version}")
        return

    for f in files:
        content = f.read_text(encoding="utf-8")
        backup(f)
        if not content.endswith("\n"):
            content += "\n"
        for code, line in new_entries:
            if f"domlp|{code}-{domino_version}|" in content:
                print(f"  ↳ {f.relative_to(target)}: {code} entry already present")
                continue
            content += line + "\n"
            print(f"  ✓ {f.relative_to(target)}: {code} entry appended")
        f.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--target", required=True,
                        help="Path to upstream domino-container clone")
    parser.add_argument("--lang", required=True,
                        help="Comma-separated language codes from language_registry.py (e.g. TC or TC,SC)")
    parser.add_argument("--domino-version", default="14.5.1",
                        help="Domino version for software.txt manifest entries (default: 14.5.1)")
    parser.add_argument("--allow-inferred", action="store_true",
                        help="Allow languages with status='inferred' (default: refuse, you'd need to verify first)")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not (target / "build.sh").is_file():
        fail(f"{target} doesn't look like a domino-container clone (no build.sh).")

    codes = [c.strip().upper() for c in args.lang.split(",") if c.strip()]

    # Look up & validate each requested language
    langs: list[tuple[str, dict]] = []
    for code in codes:
        cfg = registry.get(code)
        if cfg is None:
            fail(
                f"Unknown language: {code}. Registered: {registry.list_codes()}. "
                f"To add it, see docs/adding-new-language.md."
            )
        if cfg["status"] == "template":
            fail(
                f"[{code}] is registered but status='template' "
                f"(installer_code not yet filled). "
                f"You must verify the installer code first — see docs/adding-new-language.md."
            )
        if cfg["status"] == "inferred" and not args.allow_inferred:
            fail(
                f"[{code}] is registered with status='inferred' (NOT verified). "
                f"Re-run with --allow-inferred to proceed at your own risk, "
                f"or follow docs/adding-new-language.md to verify first."
            )
        langs.append((code, cfg))

    print(f"Target: {target}")
    print(f"Tested upstream commit: {TESTED_COMMIT}")
    print(f"Languages to apply: {[c for c, _ in langs]}")
    print(f"Domino version (manifest): {args.domino_version}\n")

    patch_buildsh(target, langs)
    patch_install_domino(target, langs)
    patch_software_txt(target, langs, args.domino_version)

    print()
    print("✅ All patches applied. Next step:")
    print(f"   cd {target}")
    print(f"   ./build.sh domino {args.domino_version} -restapi=... -leap=... " +
          " ".join(f"-domlp={c}" for c, _ in langs))
    print()
    print("   (only one -domlp flag is supported per build; build separately for each LP if needed)")


if __name__ == "__main__":
    main()
