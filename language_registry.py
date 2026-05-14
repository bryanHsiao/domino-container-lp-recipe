"""
Language Pack registry for HCL Domino Container LP integration.

This dict is the single source of truth for what languages the recipe knows
how to integrate. patch.py reads this when --lang is specified.

繁體：本字典是 recipe 的單一資料來源 — 它知道怎麼整合的所有語言。
patch.py 在指定 --lang 時會讀這個字典。

------------------------------------------------------------------------------
STATUS values / 狀態值
------------------------------------------------------------------------------
  "verified"  — installer_code confirmed via `strings LNXDomLP | grep LangCodeList`,
                AND at least one successful end-to-end build by recipe authors
                or contributors.
                installer_code 已透過 `strings LNXDomLP | grep LangCodeList`
                驗證，且 recipe 作者或貢獻者已完整 build 跑通至少一次。

  "inferred"  — installer_code based on symmetric reasoning from a verified
                language, but no actual test run. Safe to attempt, but
                installer_code may need adjustment.
                installer_code 基於對稱推論（從已驗證語言推得），但未實測。
                可以嘗試套用，但 installer_code 可能要微調。

  "template"  — placeholder. Contributor must verify installer_code before use.
                空白範本。使用者必須先驗證 installer_code 才能用。

------------------------------------------------------------------------------
HOW TO ADD A NEW LANGUAGE / 怎麼加新語言
------------------------------------------------------------------------------
1. (English) See docs/adding-new-language.md for the full walkthrough.
   (繁體) 完整教學見 docs/adding-new-language.md。

2. Quick steps / 快速步驟:
   a. Extract the LP tar and find the installer code:
      解壓 LP tar 找 installer code:
        tar xf Domino_X.Y.Z_SLP_<Language>.tar
        strings LNXDomLP | grep -iE 'LangCodeList|<expected_code>'

   b. Add an entry below with status="verified" or "inferred".
      在下方加入條目，status 標 "verified" 或 "inferred"。

   c. Apply:
      套用:
        ./apply-lp.sh --lang <CODE> --tar /path/to/lp.tar

3. After a successful build, send a PR back to this recipe with status upgraded
   to "verified" so others benefit.
   build 成功後，請發 PR 回 recipe 把 status 升為 "verified"，讓其他人受惠。
"""

# Type hint: dict of LANG_CODE -> language config
LANGUAGES = {
    # =========================================================================
    # Traditional Chinese — verified reference implementation
    # 繁體中文 — 已驗證的參考實作
    # =========================================================================
    "TC": {
        "status": "verified",
        "display_name": "Traditional Chinese",
        "keypress": "t",          # Letter to press in build.sh LP submenu
        "installer_code": "zh-TW",  # LNXDomLP internal code (verified by strings)
        # Manifest entries — keyed by Domino version. Add one per supported version.
        # SHA256 is the recipe author's tar; build.sh CHECK_HASH defaults to empty
        # so this isn't validated. If your tar differs, replace it.
        # SHA256 是 recipe 作者的 tar；build.sh CHECK_HASH 預設不驗。
        # 若你的 tar 不同，請替換。
        "manifest_entries": {
            "14.5.1": {
                "tar": "Domino_14.5.1_SLP_TChinese.tar",
                "hcl_id": "TChineseManualEntry01",
                "sha256": "b60deaab0651525e56f85f0d725c646702a806ef75bd0ad6405f30f74e2986d9",
            },
        },
    },

    # =========================================================================
    # Simplified Chinese — inferred from TC symmetry, NOT YET TESTED
    # 簡體中文 — 從 TC 對稱推論，尚未實測
    # =========================================================================
    "SC": {
        "status": "inferred",
        "display_name": "Simplified Chinese",
        "keypress": "s",
        "installer_code": "zh-CN",  # Inferred; please verify via strings LNXDomLP
        "manifest_entries": {
            # Add when you have the tar:
            # 拿到 tar 後加上:
            # "14.5.1": {
            #     "tar": "Domino_14.5.1_SLP_SChinese.tar",
            #     "hcl_id": "<5-char-or-placeholder>",
            #     "sha256": "<sha256sum-of-your-tar>",
            # },
        },
    },

    # =========================================================================
    # Korean — template, contributor must fill in
    # 韓文 — 範本，貢獻者必須填入
    # =========================================================================
    "KO": {
        "status": "template",
        "display_name": "Korean",
        "keypress": "k",
        "installer_code": None,  # MUST verify: strings LNXDomLP | grep LangCodeList
        "manifest_entries": {},
    },
}


def get(code):
    """Look up a language config by code; returns None if not registered.

    依語言碼查詢設定；找不到時回傳 None。
    """
    return LANGUAGES.get(code.upper())


def list_codes():
    """List all registered language codes.

    列出所有已註冊的語言碼。
    """
    return sorted(LANGUAGES.keys())


def list_by_status(status):
    """Filter languages by status.

    依狀態篩選語言。
    """
    return {c: cfg for c, cfg in LANGUAGES.items() if cfg["status"] == status}
