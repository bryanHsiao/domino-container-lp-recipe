# Adding a New Language / 加新語言

> Complete walkthrough for contributors who want to integrate a new HCL Domino Language Pack (e.g. Korean, Thai, Russian) into this recipe.
>
> 給想要加入新語言（例如韓文、泰文、俄文）的貢獻者的完整教學。

---

## English

### Overview

Adding language **XX** (your new language code) requires:

1. **Verifying the LP installer's internal language code** — XX may map to something different from `xx` (e.g. TC → zh-TW). Without verification, the LP installer (LNXDomLP) silently fails and the build dies with `Cannot find LPLog.txt`.
2. **Adding XX to `language_registry.py`** with status `"verified"`.
3. **Running `./apply-lp.sh --lang XX`** to patch upstream `domino-container`.
4. **Building and verifying** the resulting image really contains XX.
5. **(Optional) Sending a PR** back to this recipe so others benefit.

The challenge isn't writing code — it's collecting the right metadata. This guide walks through each piece.

### Prerequisites

- HCL Domino LP tar for your target language, e.g. `Domino_14.5.1_SLP_Korean.tar`, placed in `/local/software/`
- Working Domino container build environment (Docker / Podman, this recipe's dependencies)
- ~30 minutes for one language, end-to-end

### Step 1 — Find the installer's internal language code

This is the most critical step. The LP installer (LNXDomLP, a Java InstallAnywhere binary) has an internal `LangCodeList` mapping the language to its installation code. For ISO-639-1-compatible languages (de/es/fr/it/nl/ja/ko/th/…) the code is usually just the lowercased ISO code. For Chinese variants it's `zh-TW` / `zh-CN`. We need to confirm.

```bash
# Extract the LP tar to a scratch directory
mkdir -p /tmp/lp-inspect && cd /tmp/lp-inspect
tar xf /local/software/Domino_14.5.1_SLP_<Language>.tar

# Find the language code map
# (replace 'ko' / 'korean' with terms matching your target language)
strings LNXDomLP | grep -iE 'LangCodeList|^ko$|^kr$|korean'

# You're looking for a line like:
#   LangCodeList("ko") = "KO"
#   LangCodeList("zh-TW") = "TC"
```

If the LP installer reveals e.g. `LangCodeList("ko") = "KO"`, then the **installer_code is `ko`**. Make note.

If you can't find a definitive line, try broader greps:

```bash
strings LNXDomLP | grep -iE 'languages_00|languagepack|installLP|lang.*korean'
```

### Step 2 — Choose a keypress letter

In `build.sh`'s LP submenu, each language has a single keystroke. Existing letters in use: `d` (DE), `e` (ES), `f` (FR), `i` (IT), `n` (NL), `j` (JA), `t` (TC, added by this recipe).

For Korean, `k` is the natural choice. For your language, pick a letter:
- Not in the existing set
- Not `0` (cancel) or `q` (Quit from menu — though this is in the main menu, not submenu)
- Memorably related to the language name (English mnemonic is fine)

### Step 3 — Compute the tar's SHA256 (optional but recommended)

```bash
sha256sum /local/software/Domino_14.5.1_SLP_<Language>.tar
```

`build.sh` defaults to `CHECK_HASH=` (empty/off), so this isn't strictly required. But for reproducibility and for the day someone sets `CHECK_HASH=yes`, fill it in.

### Step 4 — Decide on an `hcl_id` placeholder

HCL's real 5-char IDs (the 4th pipe-separated field in `software.txt`) aren't publicly documented. The recipe uses `TChineseManualEntry01` for TC; you can use anything similar. `build.sh` doesn't validate this field — it's an opaque identifier.

Pattern: `<Lang>ManualEntry01` or `<Lang>Community01`.

### Step 5 — Add to `language_registry.py`

Open `language_registry.py` and add an entry to the `LANGUAGES` dict:

```python
LANGUAGES = {
    # ... existing entries ...

    "KO": {
        "status": "verified",       # since you verified the installer_code
        "display_name": "Korean",
        "keypress": "k",
        "installer_code": "ko",     # from Step 1
        "manifest_entries": {
            "14.5.1": {
                "tar": "Domino_14.5.1_SLP_Korean.tar",
                "hcl_id": "KoreanManualEntry01",
                "sha256": "<from Step 3>",
            },
        },
    },
}
```

### Step 6 — Apply the patches

```bash
./apply-lp.sh --lang KO
```

This will:
1. Reset patched files to vanilla
2. Run `patch.py --lang KO`
3. Print the build command to use next

If `apply-lp.sh` complains the anchors don't match, you may be on a newer upstream commit than the tested one — see [`../upgrade-guide.md`](../upgrade-guide.md).

### Step 7 — Build

```bash
cd /local/github/domino-container
./build.sh domino 14.5.1 -restapi=1.1.7 -leap=1.1.10 -domlp=KO
```

Typical build time: 5–6 minutes. Watch for:
- `Installing Language Pack KO-14.5.1 (KO)`
- `Selected Language Packs are successfully installed.`
- `naming to docker.io/hclcom/domino:14.5.1 done`

### Step 8 — Verify

```bash
./verify.sh --lang KO
```

The verifier checks three things:
1. Image label `DominoContainer.addons` includes `languagepack=KO`
2. Image contains `*ko*` resource directories
3. LP install log shows successful install

If you have a running container based on a **fresh data dir** (see SOP §12.6), `verify.sh --container domino-lab` will also grep for non-ASCII strings in the server console log as a sanity check that the language is actually being used.

### Step 9 — (Optional but please!) Send a PR

Help other people who want this language:

1. Fork `bryanHsiao/domino-container-lp-recipe`
2. Add your language to `language_registry.py` (status: `verified`)
3. Add a row to `tested-against.md` under your language column
4. Open a PR with a brief description: "Add Korean LP support (verified on Domino 14.5.1)"

If you only had time to verify the installer code but not run a full build, set status to `"inferred"` and note that in the PR — that's still useful to others.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `apply-lp.sh` exits with "expected N matches, found 0" | Upstream changed the anchored code | See [`../upgrade-guide.md`](../upgrade-guide.md) |
| Build dies with `Cannot find LPLog.txt` | `installer_code` wrong (your language's `LangCodeList` value differs) | Re-run Step 1, update registry, retry |
| Build dies with `ERROR - Download for [domlp] [XX-14.5.1] not found!` | `software.txt` entry not added in container-side manifest | Confirm `dockerfiles/install_dir_common/software.txt` has the entry (apply-lp.sh adds both) |
| Image builds but `verify.sh` says no `xx` resource directories | Wrong `installer_code`, or installer didn't actually deploy templates (rare) | Check `install_domlp.log` inside the image; look for `Installed Feature(s)` line |
| Newly-built image works but existing server still shows English UI | "`Data already installed`" sync trap | See SOP §12.6 — needs fresh data dir |

---

## 繁體中文

### 概觀

加入語言 **XX**（你的新語言代號）需要做：

1. **驗證 LP installer 的內部語言碼** — XX 可能對應跟 `xx` 不一樣的代號（例如 TC → zh-TW）。沒驗證的話，LP installer (LNXDomLP) 會靜默失敗，build 死在 `Cannot find LPLog.txt`。
2. **把 XX 加入 `language_registry.py`**，status 設 `"verified"`。
3. **跑 `./apply-lp.sh --lang XX`** 套 patch 到上游 `domino-container`。
4. **Build 並驗證** 出來的 image 真的含 XX。
5. **（選擇性）發 PR** 回 recipe 造福他人。

挑戰不在寫 code — 在於蒐集對的 metadata。本指南逐步教你。

### 前置條件

- 對應語言的 HCL Domino LP tar（例如 `Domino_14.5.1_SLP_Korean.tar`），放在 `/local/software/`
- 可運作的 Domino container build 環境（Docker / Podman 與本 recipe 的依賴）
- 一個語言的完整流程大約需要 30 分鐘

### 步驟 1 — 找 installer 的內部語言碼

這是最關鍵的步驟。LP installer（LNXDomLP，Java InstallAnywhere 編譯出的執行檔）內部有 `LangCodeList`，把語言對應到它的安裝代號。對 ISO-639-1 標準語言（de/es/fr/it/nl/ja/ko/th/…）通常就是 ISO 代號 lowercase。對中文是 `zh-TW` / `zh-CN`。要實際驗證。

```bash
# 解壓 LP tar 到暫存目錄
mkdir -p /tmp/lp-inspect && cd /tmp/lp-inspect
tar xf /local/software/Domino_14.5.1_SLP_<Language>.tar

# 找語言代號表
# （把 'ko' / 'korean' 換成你目標語言相關詞）
strings LNXDomLP | grep -iE 'LangCodeList|^ko$|^kr$|korean'

# 期待看到類似：
#   LangCodeList("ko") = "KO"
#   LangCodeList("zh-TW") = "TC"
```

如果 LP installer 顯示 `LangCodeList("ko") = "KO"`，那 **installer_code 就是 `ko`**。記下來。

找不到明確的話，試更廣的 grep：

```bash
strings LNXDomLP | grep -iE 'languages_00|languagepack|installLP|lang.*korean'
```

### 步驟 2 — 挑 keypress 字母

`build.sh` 的 LP 子選單每個語言有一個按鍵字母。目前用掉的：`d` (DE), `e` (ES), `f` (FR), `i` (IT), `n` (NL), `j` (JA), `t` (TC，本 recipe 加的)。

韓文 `k` 很自然。挑字母原則：
- 不跟現有重複
- 不是 `0`（取消）或 `q`（Quit，雖然這是主 menu 用、子 menu 沒用 q）
- 跟語言名稱有英文記憶連結即可

### 步驟 3 — 算 tar 的 SHA256（建議但非必要）

```bash
sha256sum /local/software/Domino_14.5.1_SLP_<Language>.tar
```

`build.sh` 預設 `CHECK_HASH=`（空 / 關），所以不嚴格需要。但為了可重現、為了未來有人開 `CHECK_HASH=yes`，請填。

### 步驟 4 — 決定 `hcl_id` 的 placeholder

HCL 真實的 5 字 ID（`software.txt` 第 4 欄）對外不公開。本 recipe 對 TC 用 `TChineseManualEntry01`；你也可以類比。`build.sh` 不驗這欄 — 它是個 opaque 識別字串。

慣例：`<Lang>ManualEntry01` 或 `<Lang>Community01`。

### 步驟 5 — 加進 `language_registry.py`

打開 `language_registry.py`，在 `LANGUAGES` dict 加條目：

```python
LANGUAGES = {
    # ... 既有條目 ...

    "KO": {
        "status": "verified",       # 因為你已驗證 installer_code
        "display_name": "Korean",
        "keypress": "k",
        "installer_code": "ko",     # 步驟 1 找到的
        "manifest_entries": {
            "14.5.1": {
                "tar": "Domino_14.5.1_SLP_Korean.tar",
                "hcl_id": "KoreanManualEntry01",
                "sha256": "<步驟 3 算出的>",
            },
        },
    },
}
```

### 步驟 6 — 套用 patch

```bash
./apply-lp.sh --lang KO
```

腳本會：
1. 把 patched 檔案還原為 vanilla
2. 跑 `patch.py --lang KO`
3. 印出 build 指令給你

如果 `apply-lp.sh` 抱怨 anchor 對不上，可能你的上游 commit 比 tested commit 更新 — 見 [`../upgrade-guide.md`](../upgrade-guide.md)。

### 步驟 7 — Build

```bash
cd /local/github/domino-container
./build.sh domino 14.5.1 -restapi=1.1.7 -leap=1.1.10 -domlp=KO
```

典型 build 時間 5–6 分鐘。關注：
- `Installing Language Pack KO-14.5.1 (KO)`
- `Selected Language Packs are successfully installed.`
- `naming to docker.io/hclcom/domino:14.5.1 done`

### 步驟 8 — 驗證

```bash
./verify.sh --lang KO
```

驗證三件事：
1. Image label `DominoContainer.addons` 包含 `languagepack=KO`
2. Image 含 `*ko*` 資源目錄
3. LP install log 顯示安裝成功

如果你有 container 跑在 **fresh data dir** 上（見 SOP §12.6），`verify.sh --container domino-lab` 還會 grep server console log 的非 ASCII 字串，作為「語言真的在跑」的 sanity check。

### 步驟 9 —（選擇性但很歡迎！）發 PR

幫其他想用這語言的人：

1. Fork `bryanHsiao/domino-container-lp-recipe`
2. 在 `language_registry.py` 加你的語言（status: `verified`）
3. 在 `tested-against.md` 加一列
4. 開 PR，簡短說明：「Add Korean LP support (verified on Domino 14.5.1)」

如果你只能驗證 installer code 但沒時間跑完整 build，設 status 為 `"inferred"` 並在 PR 寫明 — 這對其他人仍有幫助。

### 疑難排解

| 症狀 | 可能原因 | 解法 |
|---|---|---|
| `apply-lp.sh` 結束顯示「expected N matches, found 0」 | 上游改了 anchored 區段 | 見 [`../upgrade-guide.md`](../upgrade-guide.md) |
| Build 死在 `Cannot find LPLog.txt` | `installer_code` 不對（該語言的 `LangCodeList` 值不一樣）| 重做步驟 1、更新 registry、重試 |
| Build 死在 `ERROR - Download for [domlp] [XX-14.5.1] not found!` | container 端 manifest 沒加條目 | 確認 `dockerfiles/install_dir_common/software.txt` 有條目（apply-lp.sh 會同時加兩份）|
| Image build 成功但 `verify.sh` 找不到 `xx` 資源目錄 | `installer_code` 不對，或 installer 沒實際部署 templates（罕見）| 進 image 內看 `install_domlp.log`，找 `Installed Feature(s)` 那行 |
| 新 build 的 image 跑起來、但既有 server 介面仍英文 | 「Data already installed」同步陷阱 | 見 SOP §12.6 — 需要 fresh data dir |
