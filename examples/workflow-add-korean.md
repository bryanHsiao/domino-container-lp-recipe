# Example Workflow: Adding Korean (KO) / 範例：加入韓文

> Concrete walkthrough showing how someone with a `Domino_14.5.1_SLP_Korean.tar` would use this recipe to add KO support. This is illustrative — the recipe author hasn't actually run this end-to-end, but the steps mirror the TC verification.
>
> 具體範例：手上有 `Domino_14.5.1_SLP_Korean.tar` 的人怎麼用本 recipe 加 KO 支援。**範例性質** — recipe 作者沒實際跑過完整流程，但步驟對應 TC 驗證流程。

---

## English

### Scenario

Alice's company uses Domino on Korean Windows clients. She has `Domino_14.5.1_SLP_Korean.tar` from HCL FlexNet and wants the container build to include KO.

### Step 1 — Get the recipe

```bash
git clone https://github.com/bryanHsiao/domino-container-lp-recipe.git ~/lp-recipe
cd ~/lp-recipe
```

### Step 2 — Find the installer code

```bash
mkdir -p /tmp/kolp && cd /tmp/kolp
cp /local/software/Domino_14.5.1_SLP_Korean.tar .
tar xf Domino_14.5.1_SLP_Korean.tar
strings LNXDomLP | grep -iE 'LangCodeList|^ko$|korean'
```

Expected output (illustrative — actual code TBD by whoever runs this):

```
	LangCodeList("ko") = "KO"
	$SLPBLD$/ko/kitfiles/...
```

So `installer_code = "ko"`. Since `code.lower() == "ko" == installer_code`, no install_domino.sh case mapping is needed for KO. (Contrast TC, where `tc != zh-TW` so a mapping is required.)

### Step 3 — Update the registry

Edit `~/lp-recipe/language_registry.py` and change the KO entry from template to verified:

```python
"KO": {
    "status": "verified",                          # was: "template"
    "display_name": "Korean",
    "keypress": "k",
    "installer_code": "ko",                        # was: None
    "manifest_entries": {
        "14.5.1": {
            "tar": "Domino_14.5.1_SLP_Korean.tar",
            "hcl_id": "KoreanManualEntry01",       # placeholder, opaque to build.sh
            "sha256": "<output of `sha256sum Domino_14.5.1_SLP_Korean.tar`>",
        },
    },
},
```

### Step 4 — Apply patches

```bash
~/lp-recipe/apply-lp.sh --lang KO
```

Expected output:

```
[1/3] Cloning upstream HCL repo to /local/github/domino-container...
  ✓ Cloned and checked out 4734801
[2/3] Resetting LP-affected files to vanilla...
  ✓ Reset complete
[3/3] Running patch.py...
[1/3] build.sh — ...
  ✓ KO (Korean, keypress='k') — 4 edits applied
[2/3] install_domino.sh — ...
  ↳ No mappings needed for the chosen languages (installer codes match lowercased short codes)
[3/3] software.txt — appending entries for Domino 14.5.1
  ✓ software/software.txt: KO entry appended
  ✓ dockerfiles/install_dir_common/software.txt: KO entry appended

✅ All patches applied.
```

### Step 5 — Build

```bash
cd /local/github/domino-container
./build.sh domino 14.5.1 -restapi=1.1.7 -leap=1.1.10 -domlp=KO
```

Watch for log lines (estimated; based on what TC produced):

```
Installing Language Pack KO-14.5.1 (KO)
Running Domino Language Pack Silent Install -- This takes a while ...
Installed Feature(s) pfReplaceData_ko, pfReplaceCore_ko, pfaAddData_mail145_ntf_ko, ...
Selected Language Packs are successfully installed.
naming to docker.io/hclcom/domino:14.5.1 done
```

### Step 6 — Verify

```bash
~/lp-recipe/verify.sh --lang KO
```

Expected:

```
[1/3] Image label DominoContainer.addons should include languagepack=KO
  ✓ languagepack=KO,domrestapi=1.1.7-14.5,leap=1.1.10
[2/3] Image contains KO/ko resource directories
  ✓ Found 9+ path(s) matching 'ko'
[3/3] LP install log records successful install
  Selected Language Packs are successfully installed.
```

### Step 7 — Share back

If Step 6 passed, send a PR:

```bash
cd ~/lp-recipe
git checkout -b add-ko-verified
# (your registry edits are already in)
git add language_registry.py tested-against.md
# Edit tested-against.md to add a row for KO
git commit -m "Verify Korean LP integration on Domino 14.5.1"
gh pr create
```

The recipe author will review and merge — everyone else who wants KO can then just use it.

### If something fails

| Step that fails | Likely cause | Next action |
|---|---|---|
| 2 (find code) | No match for `LangCodeList` in strings output | Try broader greps; check `strings AIXDomLP` instead; ask in [`#55`](https://github.com/HCL-TECH-SOFTWARE/domino-container/issues/55) |
| 4 (apply) | Anchor mismatch (upstream changed) | See [`../upgrade-guide.md`](../upgrade-guide.md) |
| 5 (build) — `Cannot find LPLog.txt` | Wrong `installer_code` despite Step 2 | Try variants: `ko-KR`, `Korean`, etc.; update registry; retry |
| 5 — `Download for [domlp] [KO-14.5.1] not found!` | Container-side `software.txt` missing entry | Check `dockerfiles/install_dir_common/software.txt` |
| 6 — `verify.sh` finds 0 `ko` resources | Wrong `installer_code` deployed silently | Same as the Cannot-find-LPLog case |
| New build OK but existing server still English | "Data already installed" sync trap | See SOP §12.6 — needs fresh data dir |

---

## 繁體中文

### 情境

Alice 公司用 Domino 搭配韓文 Windows client。她從 HCL FlexNet 拿到 `Domino_14.5.1_SLP_Korean.tar`，希望 container build 內含 KO。

### 步驟 1 — 拿 recipe

```bash
git clone https://github.com/bryanHsiao/domino-container-lp-recipe.git ~/lp-recipe
cd ~/lp-recipe
```

### 步驟 2 — 找 installer code

```bash
mkdir -p /tmp/kolp && cd /tmp/kolp
cp /local/software/Domino_14.5.1_SLP_Korean.tar .
tar xf Domino_14.5.1_SLP_Korean.tar
strings LNXDomLP | grep -iE 'LangCodeList|^ko$|korean'
```

預期輸出（示例 — 實際碼以跑出來為準）：

```
	LangCodeList("ko") = "KO"
	$SLPBLD$/ko/kitfiles/...
```

所以 `installer_code = "ko"`。因為 `code.lower() == "ko" == installer_code`，KO 不需要 install_domino.sh case 對應。（對照 TC：`tc != zh-TW`，所以需要對應。）

### 步驟 3 — 更新 registry

編輯 `~/lp-recipe/language_registry.py`，把 KO 從 template 改成 verified：

```python
"KO": {
    "status": "verified",                          # 原本: "template"
    "display_name": "Korean",
    "keypress": "k",
    "installer_code": "ko",                        # 原本: None
    "manifest_entries": {
        "14.5.1": {
            "tar": "Domino_14.5.1_SLP_Korean.tar",
            "hcl_id": "KoreanManualEntry01",       # placeholder, build.sh 不驗
            "sha256": "<`sha256sum Domino_14.5.1_SLP_Korean.tar` 的輸出>",
        },
    },
},
```

### 步驟 4 — 套用 patch

```bash
~/lp-recipe/apply-lp.sh --lang KO
```

預期輸出：

```
[1/3] Cloning upstream HCL repo to /local/github/domino-container...
  ✓ Cloned and checked out 4734801
[2/3] Resetting LP-affected files to vanilla...
  ✓ Reset complete
[3/3] Running patch.py...
[1/3] build.sh — ...
  ✓ KO (Korean, keypress='k') — 4 edits applied
[2/3] install_domino.sh — ...
  ↳ No mappings needed for the chosen languages (installer codes match lowercased short codes)
[3/3] software.txt — appending entries for Domino 14.5.1
  ✓ software/software.txt: KO entry appended
  ✓ dockerfiles/install_dir_common/software.txt: KO entry appended

✅ All patches applied.
```

### 步驟 5 — Build

```bash
cd /local/github/domino-container
./build.sh domino 14.5.1 -restapi=1.1.7 -leap=1.1.10 -domlp=KO
```

注意關鍵 log（推估；對應 TC 的輸出）：

```
Installing Language Pack KO-14.5.1 (KO)
Running Domino Language Pack Silent Install -- This takes a while ...
Installed Feature(s) pfReplaceData_ko, pfReplaceCore_ko, pfaAddData_mail145_ntf_ko, ...
Selected Language Packs are successfully installed.
naming to docker.io/hclcom/domino:14.5.1 done
```

### 步驟 6 — 驗證

```bash
~/lp-recipe/verify.sh --lang KO
```

預期：

```
[1/3] Image label DominoContainer.addons should include languagepack=KO
  ✓ languagepack=KO,domrestapi=1.1.7-14.5,leap=1.1.10
[2/3] Image contains KO/ko resource directories
  ✓ Found 9+ path(s) matching 'ko'
[3/3] LP install log records successful install
  Selected Language Packs are successfully installed.
```

### 步驟 7 — 回饋社群

如果步驟 6 過了，請發 PR：

```bash
cd ~/lp-recipe
git checkout -b add-ko-verified
# （你的 registry 改動已經存好）
git add language_registry.py tested-against.md
# 編輯 tested-against.md 加 KO 那列
git commit -m "Verify Korean LP integration on Domino 14.5.1"
gh pr create
```

Recipe 作者會 review + merge — 其他想要 KO 的人之後就能直接用。

### 失敗時怎麼辦

| 失敗的步驟 | 可能原因 | 下一步 |
|---|---|---|
| 2（找 code）| strings 輸出沒 `LangCodeList` 命中 | 試更廣的 grep；用 `strings AIXDomLP` 看；到 [`#55`](https://github.com/HCL-TECH-SOFTWARE/domino-container/issues/55) 問 |
| 4（套用）| Anchor 不符（上游改了）| 見 [`../upgrade-guide.md`](../upgrade-guide.md) |
| 5（build）— `Cannot find LPLog.txt` | 步驟 2 找到的 `installer_code` 錯了 | 試變體：`ko-KR`、`Korean`...，更新 registry，重試 |
| 5 — `Download for [domlp] [KO-14.5.1] not found!` | container 端 `software.txt` 沒條目 | 看 `dockerfiles/install_dir_common/software.txt` |
| 6 — `verify.sh` 找不到 `ko` 資源 | `installer_code` 不對但 installer 沒報錯 | 同上 Cannot-find-LPLog 處理 |
| 新 build 成功但既有 server 介面仍英文 | 「Data already installed」同步陷阱 | 見 SOP §12.6 — 需 fresh data dir |
