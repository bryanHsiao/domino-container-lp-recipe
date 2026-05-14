# Tested Versions / 已驗證版本

---

## English

This recipe is validated against the combinations below. Each row represents one full end-to-end run by the recipe author or a contributor.

| Recipe ver | Upstream commit | Domino | Language | OS | Container engine | Result | Notes |
|---|---|---|---|---|---|---|---|
| v0.1 | [`4734801`](https://github.com/HCL-TECH-SOFTWARE/domino-container/commit/4734801) | 14.5.1 | **TC** | Ubuntu 24.04.4 (WSL2) | Docker 29.4.3 | ✅ Build + fresh-setup verified | `names.nsf` in Traditional Chinese; console.log contains 「網域監督」 |

### What "verified" means

For each row to be "verified", these must all be true:

1. ✅ `apply-lp.sh --lang <X>` completes (all anchors found)
2. ✅ `./build.sh menu` shows the language in the LP submenu
3. ✅ `./build.sh domino <VER> -domlp=<X>` completes successfully
4. ✅ Resulting image has `DominoContainer.addons` label containing `languagepack=<X>`
5. ✅ Resulting image contains language-resource directories (e.g. `zh-tw`)
6. ✅ LP install log records `Selected Language Packs are successfully installed`
7. ✅ On a fresh data dir, OneTouch Setup creates databases with localized form/view names

### Why pin to a tested commit?

Upstream `domino-container` maintainer (`@Daniel-Nashed`) commits directly to `main` (external PRs are rare — last merged external PR was 2024-07). `main` can change at any time between testers. Pinning to a known-good commit gives reproducible results.

If you want to try a newer commit, run `apply-lp.sh` with `FORCE=1`. If it succeeds, please add a row above via PR.

### Contributing a tested combination

If you've successfully used this recipe with a new combination (newer Domino, different Linux distro, Podman instead of Docker, a different language), please open a PR adding your row. Even a partial success ("builds but the [sync trap](docs/sync-trap-caveat.md) hits") is useful to document.

---

## 繁體中文

本工具在下列組合上驗證過。每一列代表作者或貢獻者實際跑過一次完整流程。

| 工具版本 | 上游 commit | Domino | 語言 | 作業系統 | 容器引擎 | 結果 | 備註 |
|---|---|---|---|---|---|---|---|
| v0.1 | [`4734801`](https://github.com/HCL-TECH-SOFTWARE/domino-container/commit/4734801) | 14.5.1 | **TC** | Ubuntu 24.04.4 (WSL2) | Docker 29.4.3 | ✅ Build + 重做 setup 驗證過 | `names.nsf` 顯示繁中；`console.log` 含「網域監督」|

### 「驗證過」是什麼意思

每一列要算「驗證過」需滿足全部條件：

1. ✅ `apply-lp.sh --lang <X>` 跑完（所有錨點找到）
2. ✅ `./build.sh menu` 在 LP 子選單顯示該語言
3. ✅ `./build.sh domino <版本> -domlp=<X>` 跑完成功
4. ✅ Image 的 `DominoContainer.addons` 標籤含 `languagepack=<X>`
5. ✅ Image 內含該語言資源目錄（例如 `zh-tw`）
6. ✅ LP 安裝紀錄寫了 `Selected Language Packs are successfully installed`
7. ✅ 在乾淨的資料目錄上跑 OneTouch Setup，建出的資料庫 form／view 名稱是該語言

### 為什麼要鎖定在已測試的 commit？

上游 `domino-container` 維護者（`@Daniel-Nashed`）直接 commit 到 `main`（外部 PR 很少 — 最後一個合併的外部 PR 是 2024-07）。`main` 隨時可能變，不同測試者看到的版本可能不同。鎖定在已知正常的 commit 才能得到可重現結果。

想試較新的 commit，跑 `apply-lp.sh` 時加 `FORCE=1`。成功的話請發 PR 加一列。

### 貢獻測試組合

如果你用本工具在新組合上跑成功（較新 Domino、不同 Linux 發行版、Podman 取代 Docker、不同語言），請發 PR 加你的一列。即使只是部分成功（「build OK 但踩到 [同步陷阱](docs/sync-trap-caveat.md)」），也對其他人有參考價值。
