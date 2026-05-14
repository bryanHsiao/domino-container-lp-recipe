# How It Works / 工作原理

> Technical reference: what `patch.py` does, why each patch is needed, and how the registry maps to code edits.
>
> 技術參考：`patch.py` 做了什麼、每個 patch 為何需要、registry 怎麼對應到實際 code edit。

---

## English

### The three layers of LP integration

| Layer | File | What this recipe does |
|---|---|---|
| 1. UI / menu | `build.sh` | Add the language to LP submenu so users can select it |
| 2. Install logic | `dockerfiles/install_dir_domino/install_domino.sh` | Map non-ISO short codes to LP installer's internal codes |
| 3. Manifest | `software/software.txt` + `dockerfiles/install_dir_common/software.txt` | Tell `build.sh` what LP tar file corresponds to which lang/version |

All three are needed. If you skip the manifest, you get `Download for [domlp] [XX-VER] not found!`. If you skip the install_domino.sh mapping, you get `Cannot find LPLog.txt`. If you skip build.sh, the LP menu doesn't show the new language.

### Layer 1: build.sh — 4 anchored edits

The LP menu is hardcoded in two functions:

```
get_language_pack_display_name()  ← maps SELECT_DOMLP_LANG to display name
select_language_pack()            ← prints submenu and reads keypress
```

For each language XX, this recipe inserts:

1. **P1**: `local LP_XX="<Display Name>"` in **both** functions (after `LP_JA`)
2. **P2**: a `XX) DISPLAY_DOMLP="$LP_XX" ;;` case in `get_language_pack_display_name()`
3. **P3**: a `print_lp "XX" "$LP_XX"` line in `select_language_pack()`
4. **P4**: a `<keypress>) SELECT_DOMLP_LANG=XX ;;` case in `select_language_pack()`

The anchors all relate to `JA` (the last upstream-supported language). When applying multiple languages, the script anchors each new one between `JA` and the next case (`*)` or `esac`), preserving order across languages.

### Layer 2: install_domino.sh — case mapping

`install_domino.sh` derives the LP installer's language code by lowercasing the prefix of `DOMLP_VER`:

```bash
local DOMLP_LANG_LCASE=$(echo "$DOMLP_VER" | cut -d"-" -f1 | awk '{print tolower($0)}')
```

For `DOMLP_VER=TC-14.5.1`, that gives `tc`. The LP installer (LNXDomLP) reads this from its silent install INI as `LANGUAGES_00=tc`. But LNXDomLP's internal `LangCodeList` says `LangCodeList("zh-TW") = "TC"` — it expects `zh-TW`, not `tc`. So the silent install runs but installs nothing and exits without writing `LPLog.txt`. The build then fails with `Cannot find LPLog.txt in /opt/hcl/domino`.

The recipe inserts a `case` statement after the lowercase assignment to map non-ISO short codes:

```bash
case "$DOMLP_LANG_LCASE" in
  tc) DOMLP_LANG_LCASE=zh-TW ;;
  sc) DOMLP_LANG_LCASE=zh-CN ;;
esac
```

For languages whose `installer_code` matches the lowercased short code (e.g. `KO` → `ko`), no mapping is needed and the recipe doesn't add a line.

### Layer 3: software.txt — manifest

There are **two** copies of `software.txt` in upstream:

| File | Used by | When |
|---|---|---|
| `software/software.txt` | `build.sh` | Host-side pre-build sanity check ("does this file exist in /local/software/?") |
| `dockerfiles/install_dir_common/software.txt` | `install_domino.sh` (inside container) | Container-side: `grep "domlp\|XX-VER\|"` to find the LP tar filename |

The two files have identical content but serve different purposes. The recipe appends the same line to both:

```
domlp|XX-VER|Domino_VER_SLP_<Lang>.tar|<hcl_id>|<sha256>
```

Format: `<type>|<lang-version>|<filename>|<hcl_id>|<sha256>`

Fields:
- `type` = `domlp` (Domino Language Pack)
- `lang-version` = e.g. `TC-14.5.1`
- `filename` = name of the tar file in `/local/software/`
- `hcl_id` = HCL's internal 5-char identifier (not publicly known; recipe uses placeholders like `TChineseManualEntry01`)
- `sha256` = SHA-256 of the tar (only validated if `CHECK_HASH=yes`, which is not the default)

### How registry maps to code edits

For each entry in `language_registry.py`:

```python
"TC": {
    "status": "verified",
    "display_name": "Traditional Chinese",  # → P1's LP_TC value
    "keypress": "t",                        # → P4's case letter
    "installer_code": "zh-TW",              # → install_domino.sh case body
    "manifest_entries": {
        "14.5.1": {
            "tar": "Domino_14.5.1_SLP_TChinese.tar",
            "hcl_id": "TChineseManualEntry01",
            "sha256": "b60deaab...",
        },
    },
},
```

- `display_name` flows into the `LP_TC="..."` variable
- `keypress` flows into the `t)` case
- `installer_code` (if different from `code.lower()`) flows into the install_domino.sh mapping
- `manifest_entries[VER]` flows into the software.txt entry

### Idempotency strategy

The recipe patches against **vanilla upstream every time**:

1. `apply-lp.sh` runs `git checkout --` on the 4 affected files first
2. Then `patch.py` operates on a known-vanilla state

This means:
- Re-running with the same `--lang` is safe — same result
- Adding a new language (e.g. running with `--lang TC,KO` after previously `--lang TC`) reapplies both
- No "incremental anchor chase" complexity

The trade-off is: you can't have local manual edits to those 4 files survive. If you've also locally customized `build.sh` for something else, save your changes elsewhere before running `apply-lp.sh`.

### Tested upstream

This recipe is tested against upstream commit [`4734801`](https://github.com/HCL-TECH-SOFTWARE/domino-container/commit/4734801) ("Add Domino 12.0.2FP8"). When upstream moves, the anchors may need updates — see [`../upgrade-guide.md`](../upgrade-guide.md).

---

## 繁體中文

### LP 整合的三層

| 層級 | 檔案 | 本 recipe 做的事 |
|---|---|---|
| 1. UI / menu | `build.sh` | 把語言加入 LP 子選單，讓使用者能選 |
| 2. 安裝邏輯 | `dockerfiles/install_dir_domino/install_domino.sh` | 把非 ISO 短碼對應到 LP installer 的內部碼 |
| 3. Manifest | `software/software.txt` + `dockerfiles/install_dir_common/software.txt` | 告訴 `build.sh` 哪個 LP tar 對應哪個語言/版本 |

三層都要做。漏 manifest → `Download for [domlp] [XX-VER] not found!`；漏 install_domino.sh → `Cannot find LPLog.txt`；漏 build.sh → menu 不顯示新語言。

### 第 1 層：build.sh — 4 處錨點 edit

LP menu 寫死在兩個函式：

```
get_language_pack_display_name()  ← 把 SELECT_DOMLP_LANG 對應到顯示名稱
select_language_pack()            ← 印子選單、讀按鍵
```

對每個語言 XX，recipe 插入：

1. **P1**：`local LP_XX="<顯示名稱>"`，**兩個函式都加**（在 `LP_JA` 之後）
2. **P2**：`XX) DISPLAY_DOMLP="$LP_XX" ;;` case 在 `get_language_pack_display_name()`
3. **P3**：`print_lp "XX" "$LP_XX"` 在 `select_language_pack()`
4. **P4**：`<keypress>) SELECT_DOMLP_LANG=XX ;;` case 在 `select_language_pack()`

所有 anchor 都跟 `JA`（上游最後一個內建語言）有關。多個語言一起套時，腳本把每個新語言夾在 `JA` 跟下個 case（`*)` 或 `esac`）之間，順序由語言代號的排序保留。

### 第 2 層：install_domino.sh — case 對應

`install_domino.sh` 用 `DOMLP_VER` 的前綴 lowercase 來推 LP installer 的語言碼：

```bash
local DOMLP_LANG_LCASE=$(echo "$DOMLP_VER" | cut -d"-" -f1 | awk '{print tolower($0)}')
```

對 `DOMLP_VER=TC-14.5.1`，會得 `tc`。LP installer（LNXDomLP）從 silent install INI 讀到 `LANGUAGES_00=tc`。但 LNXDomLP 內部 `LangCodeList` 寫的是 `LangCodeList("zh-TW") = "TC"` — 它期待 `zh-TW`，不是 `tc`。所以 silent install 執行了但什麼都沒裝，也沒寫 `LPLog.txt`。Build 後面就死在 `Cannot find LPLog.txt in /opt/hcl/domino`。

Recipe 在 lowercase 賦值後插入 case statement 把非 ISO 碼對應過去：

```bash
case "$DOMLP_LANG_LCASE" in
  tc) DOMLP_LANG_LCASE=zh-TW ;;
  sc) DOMLP_LANG_LCASE=zh-CN ;;
esac
```

對 `installer_code` 跟 lowercased 短碼相同的語言（例如 `KO` → `ko`），不需要對應，recipe 不會加那行。

### 第 3 層：software.txt — manifest

上游有**兩份** `software.txt`：

| 檔案 | 誰用 | 何時 |
|---|---|---|
| `software/software.txt` | `build.sh` | Host 端 pre-build sanity check（「`/local/software/` 內有這檔嗎？」）|
| `dockerfiles/install_dir_common/software.txt` | container 內的 `install_domino.sh` | Container 端：`grep "domlp\|XX-VER\|"` 找對應 LP tar 檔名 |

兩份內容相同但用途不同。Recipe 對兩份都 append 同一行：

```
domlp|XX-VER|Domino_VER_SLP_<Lang>.tar|<hcl_id>|<sha256>
```

格式：`<類型>|<語言-版本>|<檔名>|<hcl_id>|<sha256>`

各欄位：
- `類型` = `domlp`（Domino Language Pack）
- `語言-版本` = 例如 `TC-14.5.1`
- `檔名` = `/local/software/` 內 tar 檔名
- `hcl_id` = HCL 內部 5 字識別字（對外不公開；recipe 用 `TChineseManualEntry01` 等 placeholder）
- `sha256` = tar 的 SHA-256（只有 `CHECK_HASH=yes` 才驗，預設不驗）

### Registry 怎麼對應到 code edit

對 `language_registry.py` 內每個條目：

```python
"TC": {
    "status": "verified",
    "display_name": "Traditional Chinese",  # → P1 的 LP_TC 值
    "keypress": "t",                        # → P4 的 case 字母
    "installer_code": "zh-TW",              # → install_domino.sh case 內容
    "manifest_entries": {
        "14.5.1": {
            "tar": "Domino_14.5.1_SLP_TChinese.tar",
            "hcl_id": "TChineseManualEntry01",
            "sha256": "b60deaab...",
        },
    },
},
```

- `display_name` → `LP_TC="..."` 變數值
- `keypress` → `t)` case
- `installer_code`（與 `code.lower()` 不同時）→ install_domino.sh case 對應
- `manifest_entries[VER]` → software.txt 條目

### 冪等性策略

Recipe 永遠對 **vanilla 上游**套 patch：

1. `apply-lp.sh` 先對 4 個受影響檔案跑 `git checkout --`
2. 然後 `patch.py` 對 known-vanilla 狀態操作

所以：
- 用同樣 `--lang` 重跑沒問題 — 結果一致
- 加新語言（例如先前 `--lang TC`，現在 `--lang TC,KO`）會兩個都重套
- 不需要「增量 anchor 追蹤」這種複雜度

代價是：那 4 個檔案的本地手動修改不會保留。如果你還對 `build.sh` 做了其他客製，跑 `apply-lp.sh` 前先把改動存到別處。

### Tested 上游版本

本 recipe 針對上游 commit [`4734801`](https://github.com/HCL-TECH-SOFTWARE/domino-container/commit/4734801)（"Add Domino 12.0.2FP8"）測試。上游有改動時，anchor 可能要更新 — 見 [`../upgrade-guide.md`](../upgrade-guide.md)。
