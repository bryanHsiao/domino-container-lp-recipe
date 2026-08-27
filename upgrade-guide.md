# Upgrade Guide — When Upstream Changes / 上游變動時的更新指南

---

## English

If `patch.py` fails with "expected N matches, found 0", upstream's `build.sh` or `install_domino.sh` has changed in the area we patch.

### Diagnosing

```bash
cd /local/github/domino-container

# What's changed since the tested commit?
git fetch origin
git log --oneline 4734801..origin/main -- \
  build.sh \
  dockerfiles/install_dir_domino/install_domino.sh \
  dockerfiles/install_dir_common/software.txt \
  software/software.txt

# See the actual diff for build.sh
git diff 4734801..origin/main -- build.sh

# Where do anchors fall in latest upstream?
git checkout origin/main -- build.sh
grep -n 'LP_JA\|select_language_pack\|get_language_pack_display_name' build.sh
```

### Updating `patch.py`

In `patch.py`, the `patch_buildsh()` function uses four anchor strings. Each is built from a small piece of upstream context. To update:

1. Find the new surrounding code in latest upstream (e.g. `LP_JA="Japanese"` is now somewhere else? Probably not — but check)
2. If the anchor is no longer unique, widen the context
3. If the anchor block structure changed (e.g. upstream changed `case` to `if`), the patch logic itself needs rework

The four anchors:
- **P1**: `'  local LP_JA="Japanese"\n'` (expects 2 matches across both functions)
- **P2**: the `JA) ... ;;` block immediately before `*)`
- **P3**: `print_lp "JA" "$LP_JA"` line in submenu
- **P4**: the `j) ... ;;` block immediately before `esac`

Run the tests:

```bash
rm -rf /tmp/dc-test
./apply-lp.sh --lang TC --target /tmp/dc-test/domino-container
cd /tmp/dc-test/domino-container

# Quick sanity check (no full build needed)
grep -c 'LP_TC=' build.sh                                            # expect: 2
grep -c 'TC)\|t)' build.sh                                            # expect: ≥3
grep -c 'tc) DOMLP_LANG_LCASE=zh-TW' dockerfiles/install_dir_domino/install_domino.sh  # expect: 1
grep 'domlp|TC-14.5.1' software/software.txt                          # expect: 1 match
```

If the sanity check passes, do a real build (~5 min) and update [`tested-against.md`](tested-against.md) with the new commit.

### What if patches still work but the test build fails differently?

A different failure (not anchor-related) means upstream's internal logic changed:
- LP installer expects a different INI key? — Adjust `install_domino.sh` patch
- Software check became hash-mandatory? — Set `CHECK_HASH=` env in build
- Build step renamed? — Read the docker logs carefully

These are out-of-scope for "just update anchors"; they may require a recipe rework. Open an issue with the build log.

### Why this should be rare

The patched areas — `select_language_pack()`, `get_language_pack_display_name()`, the LP install section, and `software.txt` format — have been stable since 2022. Daniel's recent commits to `main` are typically:

- New product version entries
- Bug fixes in unrelated areas (Traveler, SafeLinx, OnTime)
- README / typo fixes

So `patch.py` should keep working across most upstream commits. When it does break, the breakage is **loud** (assertion fails with a clear message), not silent.

### Happy path: upstream natively supports this

If HCL merges a PR that natively supports TC/SC/KO etc. in `build.sh menu`, this recipe becomes obsolete. In that case:

1. Add a `DEPRECATED.md`
2. Update README first paragraph: "✅ Upstream now natively supports these languages."
3. Archive the repo via GitHub UI

That'd be a happy outcome. The companion `PR-DRAFT-tc.md` and `PR-DRAFT-framework.md` are this recipe's contribution toward making that happen.

### R12 FP CLI arg gotcha (12.0.2FP*, 12.0.1FP*)

If you build R12 with a fix pack, **you MUST pass the FP as a separate arg**:

```bash
# ✅ CORRECT
./build.sh domino 12.0.2 fp8 -restapi=1.1.7 -domlp=TC

# ❌ WRONG — silently swallows FP into version, then fails at install
./build.sh domino 12.0.2FP8 -restapi=1.1.7 -domlp=TC
```

**Why**: upstream `build.sh` CLI matches version arg with `case`:

```
9*|10*|11*|12*|14*|v12*|v14*) PROD_VER=$a ;;
```

Passing `12.0.2FP8` gets swallowed whole into `PROD_VER`, and `PROD_FP` stays empty. The R12 FP tar (`Domino_1202FPn_Linux.tar`) is a **patch-only tar** with the installer at `linux64/domino/install` (not `linux64/install`). With empty `PROD_FP`, `install_domino.sh` treats the FP tar as if it were the base GA installer, fails to find `./install` under `linux64/`, and errors:

```
/tmp/install/install_domino.sh: line 228: ./install: No such file or directory
ERROR - Domino Installation failed - Cannot find installer log
```

The separate `fp*)` CLI matcher (undocumented in `-h`) sets `PROD_FP=FP8`, which then makes `install_domino.sh` download BOTH the GA and FP tars and apply the FP layer correctly.

**Impact on `DOMLP_VER`**: with correct FP arg, `PROD_VER=12.0.2` (not `12.0.2FP8`), so `DOMLP_VER=TC-12.0.2` — this matches the `manifest_entries["12.0.2"]` in `language_registry.py`. If you pass FP wrong, `DOMLP_VER=TC-12.0.2FP8` won't match and LP gets skipped.

R14 tars (14.5, 14.5.1) don't hit this because they don't have separate FP releases — everything is in the base tar.

---

## 繁體中文

如果 `patch.py` 失敗顯示「expected N matches, found 0」，代表上游的 `build.sh` 或 `install_domino.sh` 在我們套用修補的區段改了。

### 診斷

```bash
cd /local/github/domino-container

# 自從測試過的 commit 之後改了什麼？
git fetch origin
git log --oneline 4734801..origin/main -- \
  build.sh \
  dockerfiles/install_dir_domino/install_domino.sh \
  dockerfiles/install_dir_common/software.txt \
  software/software.txt

# 看 build.sh 的實際差異
git diff 4734801..origin/main -- build.sh

# 看錨點在最新上游的位置
git checkout origin/main -- build.sh
grep -n 'LP_JA\|select_language_pack\|get_language_pack_display_name' build.sh
```

### 更新 `patch.py`

`patch.py` 內的 `patch_buildsh()` 函式用 4 個錨點字串。每個錨點由一小段上游的程式碼上下文組成。更新方式：

1. 找新的上游周邊程式碼（例如 `LP_JA="Japanese"` 現在是不是在別處？通常不會，但要查）
2. 如果錨點不再唯一，把上下文拉長
3. 如果錨點所在區塊結構改了（例如上游把 `case` 改成 `if`），修補邏輯本身要重做

四個錨點：
- **P1**：`'  local LP_JA="Japanese"\n'`（兩個函式各一，預期出現 2 次）
- **P2**：`JA) ... ;;` 區塊接到 `*)` 之前
- **P3**：子選單內 `print_lp "JA" "$LP_JA"` 那行
- **P4**：`j) ... ;;` 區塊接到 `esac` 之前

跑測試：

```bash
rm -rf /tmp/dc-test
./apply-lp.sh --lang TC --target /tmp/dc-test/domino-container
cd /tmp/dc-test/domino-container

# 快速檢查（不用真的 build）
grep -c 'LP_TC=' build.sh                                            # 預期: 2
grep -c 'TC)\|t)' build.sh                                            # 預期: ≥3
grep -c 'tc) DOMLP_LANG_LCASE=zh-TW' dockerfiles/install_dir_domino/install_domino.sh  # 預期: 1
grep 'domlp|TC-14.5.1' software/software.txt                          # 預期: 1 個結果
```

檢查過了，跑一次真的 build（約 5 分鐘），然後更新 [`tested-against.md`](tested-against.md) 加新 commit。

### 如果修補套用 OK 但 build 以其他方式失敗？

不同類型的失敗（非錨點相關）表示上游的內部邏輯改了：
- LP 安裝程式預期不同的 INI 鍵？ → 改 `install_domino.sh` 修補
- 軟體檢查變成強制驗 hash？ → build 時設 `CHECK_HASH=` 環境變數
- Build 步驟改名？ → 仔細讀 docker logs

這些超出「只更新錨點」範圍；可能需要重新設計本工具。請開 issue 並附上 build 紀錄。

### 為什麼這應該很少發生

被修補的區段 — `select_language_pack()`、`get_language_pack_display_name()`、LP 安裝段、`software.txt` 格式 — 自 2022 年以來都很穩定。Daniel 最近 commit 到 `main` 的內容通常是：

- 新產品版本條目
- 不相關區域的 bug 修復（Traveler、SafeLinx、OnTime）
- README ／拼字修正

所以 `patch.py` 在大多數上游 commit 上應該繼續可用。真的壞了的時候，會**明顯**壞（assert 失敗加清楚的錯誤訊息），不會默默壞。

### 最理想的結局：上游原生支援

如果 HCL 合併了原生支援 TC／SC／KO 等語言的 PR，本工具就過時了。屆時：

1. 加一個 `DEPRECATED.md`
2. 更新 README 第一段：「✅ 上游已原生支援這些語言。」
3. 從 GitHub 介面封存這個 repo

那會是最好的結局。本 repo 內的 `PR-DRAFT-tc.md` 和 `PR-DRAFT-framework.md` 就是本工具對「促成這結局」的貢獻。

### R12 FP CLI arg 陷阱（12.0.2FP*, 12.0.1FP*）

要 build R12 帶 FP 時，**必須把 FP 當獨立 arg 傳**：

```bash
# ✅ 正確
./build.sh domino 12.0.2 fp8 -restapi=1.1.7 -domlp=TC

# ❌ 錯誤 — FP 會被吞進 version、然後在 install 階段炸掉
./build.sh domino 12.0.2FP8 -restapi=1.1.7 -domlp=TC
```

**原因**：上游 `build.sh` CLI 用 case regex 比對版本 arg：

```
9*|10*|11*|12*|14*|v12*|v14*) PROD_VER=$a ;;
```

傳 `12.0.2FP8` 整串會被 `12*` 吃掉塞進 `PROD_VER`，`PROD_FP` 保持空。R12 的 FP tar（`Domino_1202FPn_Linux.tar`）是 **patch-only tar**、內含的 `install` 執行檔在 `linux64/domino/install`（不在 `linux64/install`）。`PROD_FP` 空時、`install_domino.sh` 把 FP tar 當 base GA installer 處理、找不到 `linux64/install`、噴：

```
/tmp/install/install_domino.sh: line 228: ./install: No such file or directory
ERROR - Domino Installation failed - Cannot find installer log
```

分開傳（`fp*)` 是獨立 CLI matcher，`-h` 內沒列）會設 `PROD_FP=FP8`、然後 `install_domino.sh` 就會**分別下載 GA + FP tar、把 FP 疊上去**的正確流程。

**對 `DOMLP_VER` 的影響**：分開傳 FP 時 `PROD_VER=12.0.2`（不是 `12.0.2FP8`），所以 `DOMLP_VER=TC-12.0.2` — 這對到 `language_registry.py` 內 `manifest_entries["12.0.2"]` 條目。傳錯的話 `DOMLP_VER=TC-12.0.2FP8` 對不到、LP 就會被 skip。

R14 tar（14.5、14.5.1）不會踩這個坑，因為它們沒有分開的 FP release、所有 patch 都在 base tar 內。
