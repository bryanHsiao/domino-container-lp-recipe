# Why a Recipe, Not a Fork? / 為什麼用 Recipe 而非 Fork？

---

## English

When integrating a community LP patch, three patterns are possible:

| Pattern | What it is |
|---|---|
| **Fork** | Long-running mirror of upstream with patches committed on top |
| **Recipe** (this repo) | Small script that patches a fresh upstream clone on demand |
| **Patch series** | `git format-patch` files applied via `git am` |

### Why this repo picks recipe

The change is small: ~50 lines across 4 files. The upstream is actively developed by someone else (`Daniel-Nashed`) with a non-PR-driven workflow (commits go directly to `main`). A fork would be 99% upstream code + 1% ours, generating constant rebase noise.

A recipe **separates "what we change" from "the rest of the codebase"**, which is the right abstraction when the change is small and the upstream is moving.

### Comparison

| Aspect | Fork | Recipe | Patch series |
|---|---|---|---|
| User: first use | `clone fork && build` | `clone recipe && apply && build` | `clone upstream && clone series && git am && build` |
| User: after upstream changes | re-clone fork — may be stale | `apply-lp.sh` always uses tested commit | new patch series releases |
| Maintainer: upstream changes a file we DON'T patch | rebase noise | nothing | nothing |
| Maintainer: upstream changes a file we DO patch | rebase + per-file merge conflict resolution | update 1 anchor string in `patch.py` | regenerate patch from new fork |
| Repo size | inherits 600+ upstream commits + history | ~300 lines of code/docs | ~10 KB of patches |
| If maintainer is busy for 3 months | fork silently drifts | recipe pinned to last tested commit; users see "tested vs HEAD differs" warning | series may not apply to newer upstream |
| Sending PR to HCL | already in fork structure | `git format-patch` from a temp branch | series IS the PR |
| Mental model for "I just want it to work" | "use the fork as my upstream" | "use upstream + this tool" | "apply these patches to upstream" |

### When a fork is the right choice instead

A fork is appropriate when:
- The fork itself is the product (e.g. Forgejo ← Gitea, Valkey ← Redis)
- You commit to mirroring upstream long-term
- The patches are large enough that they're more comfortable as commits than as string anchors
- You need to ship binary releases

For "I patched 4 files in someone else's repo and want to share with my team", a recipe is lighter, more honest about scope, and easier to keep healthy.

### Hybrid: this repo includes both shapes

- **`patch.py` + `apply-lp.sh`** — for end users (recipe UX)
- **`PR-DRAFT-tc.md`** — for upstreaming (patch-series content, ready to convert via `git format-patch` to a PR)

---

## 繁體中文

整合社群 LP 修補有三種模式可選：

| 模式 | 是什麼 |
|---|---|
| **Fork** | 長期同步上游的鏡像，在上面 commit 修補 |
| **動態修補**（本工具走這條路線） | 小型腳本，對乾淨的上游 clone 動態套用修補 |
| **修補檔系列** | 用 `git am` 套用 `git format-patch` 產生的檔案 |

### 為什麼本工具選動態修補

改動範圍很小：4 個檔案、約 50 行。上游被別人（`Daniel-Nashed`）積極維護，且**走非 PR 流程**（直接 commit 到 `main`）。fork 會變成「99% 上游程式碼 + 1% 我們的」，產生持續的 rebase 噪音。

動態修補只記錄「我們改什麼」，不複製整份上游程式碼。改動小的時候比 fork 輕、跟得上上游變動。

### 比較

| 面向 | Fork | 動態修補 | 修補檔系列 |
|---|---|---|---|
| 使用者：首次使用 | `clone fork && build` | `clone 本工具 && 套用 && build` | `clone 上游 && clone 修補系列 && git am && build` |
| 使用者：上游有改動之後 | 重新 clone fork — 可能已過期 | `apply-lp.sh` 永遠用測試過的 commit | 重新發布修補檔系列 |
| 維護者：上游改了我們**不**修補的檔案 | rebase 噪音 | 無事 | 無事 |
| 維護者：上游改了我們**有**修補的檔案 | rebase + 逐檔解衝突 | 改 `patch.py` 內 1 個錨點字串 | 從新 fork 重新產生修補檔 |
| Repo 大小 | 繼承上游 600+ commits + 完整歷史 | 約 300 行程式碼／文件 | 約 10 KB 修補檔 |
| 維護者忙 3 個月 | fork 默默過期 | 本工具仍指向最後測試過的 commit；使用者看到「tested 與 HEAD 不同」警告 | 修補檔系列可能對較新上游無法套用 |
| 對 HCL 發 PR | fork 結構本來就適合發 PR | 從暫存分支跑 `git format-patch` | 修補檔系列本身就是 PR |
| 「我只想跑起來」的心智模型 | 「用 fork 當我的上游」 | 「用上游 + 這個工具」 | 「對上游套這些修補」 |

### 什麼情況用 fork 反而比較對

Fork 適合：
- Fork 本身就是產品（例如 Forgejo 之於 Gitea、Valkey 之於 Redis）
- 你承諾長期同步上游
- 修補大到「以 commit 形式管理比用字串錨點舒服」
- 你需要發布二進位 releases

對「我在別人的 repo 改 4 個檔案、想分享給同事」這種情境，動態修補更輕（repo 內只有修補腳本、不夾帶整份上游程式碼）、長期維護成本也低。

### 混合：本 repo 兩種形態都有

- **`patch.py` + `apply-lp.sh`** — 給終端使用者（動態修補體驗）
- **`PR-DRAFT-tc.md`** — 給上游 PR（修補檔系列內容，可用 `git format-patch` 一步轉成 PR）
