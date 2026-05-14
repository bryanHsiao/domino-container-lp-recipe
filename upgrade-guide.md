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

---

## 繁體中文

如果 `patch.py` 失敗顯示「expected N matches, found 0」，上游的 `build.sh` 或 `install_domino.sh` 在我們 patch 的區段改了。

### 診斷

```bash
cd /local/github/domino-container

# 自從 tested commit 之後改了什麼？
git fetch origin
git log --oneline 4734801..origin/main -- \
  build.sh \
  dockerfiles/install_dir_domino/install_domino.sh \
  dockerfiles/install_dir_common/software.txt \
  software/software.txt

# 看 build.sh 的實際 diff
git diff 4734801..origin/main -- build.sh

# 看 anchor 在 latest 上游的位置
git checkout origin/main -- build.sh
grep -n 'LP_JA\|select_language_pack\|get_language_pack_display_name' build.sh
```

### 更新 `patch.py`

`patch.py` 內 `patch_buildsh()` 函式用 4 個 anchor 字串。每個 anchor 由一小段上游 context 組成。更新方式：

1. 找新的上游周邊 code（例如 `LP_JA="Japanese"` 現在是不是在別處？通常不會，但要查）
2. 如果 anchor 不再唯一，把 context 拉長
3. 如果 anchor 區塊結構改了（例如上游把 `case` 改成 `if`），patch 邏輯本身要重做

四個 anchor：
- **P1**：`'  local LP_JA="Japanese"\n'`（兩個函式各一，預期 count=2）
- **P2**：`JA) ... ;;` 區塊接到 `*)` 之前
- **P3**：子選單內 `print_lp "JA" "$LP_JA"` 行
- **P4**：`j) ... ;;` 區塊接到 `esac` 之前

跑測試：

```bash
rm -rf /tmp/dc-test
./apply-lp.sh --lang TC --target /tmp/dc-test/domino-container
cd /tmp/dc-test/domino-container

# 快速 sanity check（不用真 build）
grep -c 'LP_TC=' build.sh                                            # 預期: 2
grep -c 'TC)\|t)' build.sh                                            # 預期: ≥3
grep -c 'tc) DOMLP_LANG_LCASE=zh-TW' dockerfiles/install_dir_domino/install_domino.sh  # 預期: 1
grep 'domlp|TC-14.5.1' software/software.txt                          # 預期: 1 match
```

Sanity check 過了，跑一次真 build（~5 分鐘），然後更新 [`tested-against.md`](tested-against.md) 加新 commit。

### 如果 patches 套用 OK 但 build 用其他方式壞了？

不同類型的失敗（非 anchor 相關）表示上游的內部邏輯改了：
- LP installer 預期不同 INI key？ → 改 `install_domino.sh` patch
- Software check 變成強制驗 hash？ → build 時設 `CHECK_HASH=` 環境變數
- Build step 改名？ → 仔細讀 docker logs

這些超出「只更新 anchor」範圍；可能需要 recipe 重做。請開 issue 附 build log。

### 為什麼這應該很少發生

被 patch 的區段 — `select_language_pack()`、`get_language_pack_display_name()`、LP install 段、`software.txt` 格式 — 自 2022 年以來都穩定。Daniel 最近的 `main` commits 通常是：

- 新產品版本條目
- 不相關區域的 bug 修復（Traveler、SafeLinx、OnTime）
- README / typo

所以 `patch.py` 在大多數上游 commits 應該繼續可用。真的壞了的時候，會**明顯**壞（assertion fail 加清楚訊息），不會默默壞。

### Happy path：上游原生支援

如果 HCL 合併了原生支援 TC/SC/KO 等語言的 PR，本 recipe 就過時了。屆時：

1. 加一個 `DEPRECATED.md`
2. 更新 README 第一段：「✅ Upstream now natively supports these languages.」
3. 從 GitHub UI archive 這個 repo

那會是最好的結局。本 repo 內的 `PR-DRAFT-tc.md` 和 `PR-DRAFT-framework.md` 就是 recipe 對「促成這結局」的貢獻。
