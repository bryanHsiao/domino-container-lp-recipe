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

整合社群 LP patch 有三種模式可選：

| 模式 | 是什麼 |
|---|---|
| **Fork** | 長期同步上游的 mirror，在上面 commit patches |
| **Recipe**（本 repo） | 小型腳本，對 fresh 的上游 clone 動態套 patch |
| **Patch series** | 用 `git am` 套 `git format-patch` 檔 |

### 為什麼本 repo 選 recipe

改動範圍很小：4 個檔案、約 50 行。上游被別人（`Daniel-Nashed`）積極維護，且**走 non-PR 流程**（直接 commit 到 `main`）。fork 會變成「99% 上游 code + 1% 我們的」，產生持續的 rebase 噪音。

Recipe **把「我們改什麼」和「整個 codebase」分離**，對「改動小 + 上游持續變動」的情境是對的抽象。

### 比較

| 面向 | Fork | Recipe | Patch series |
|---|---|---|---|
| 使用者：首次使用 | `clone fork && build` | `clone recipe && apply && build` | `clone upstream && clone series && git am && build` |
| 使用者：上游有改動之後 | 重 clone fork — 可能已過期 | `apply-lp.sh` 永遠用 tested commit | 重新發布 patch series |
| 維護者：上游改了我們**不** patch 的檔案 | rebase 噪音 | 無事 | 無事 |
| 維護者：上游改了我們**有** patch 的檔案 | rebase + 逐檔解 conflict | 改 `patch.py` 內 1 個 anchor 字串 | 從新 fork 重產 patch |
| Repo 大小 | 繼承 600+ 上游 commits + history | ~300 行 code/docs | ~10 KB patches |
| 維護者忙 3 個月 | fork 默默過期 | recipe pin 在 last tested commit；使用者看到「tested vs HEAD 不同」警告 | series 可能對較新上游無法套用 |
| 對 HCL 發 PR | fork 結構本來就是 PR-ready | 從 temp branch 跑 `git format-patch` | series 本身就是 PR |
| 「我只想跑起來」的心智模型 | 「用 fork 當我的 upstream」 | 「用上游 + 這個工具」 | 「對上游套這些 patches」 |

### 什麼情況用 fork 反而比較對

Fork 適合：
- Fork 本身就是產品（例如 Forgejo ← Gitea、Valkey ← Redis）
- 你承諾長期同步上游
- Patches 大到「commit 比 string anchor 更舒服」
- 你需要發布 binary releases

對「我在別人的 repo 改 4 個檔案、想分享給同事」這種情境，recipe 更輕、對 scope 更誠實、長期更健康。

### Hybrid：本 repo 兩種形態都有

- **`patch.py` + `apply-lp.sh`** — 給終端使用者（recipe UX）
- **`PR-DRAFT-tc.md`** — 給上游 PR（patch-series 內容，可用 `git format-patch` 一步轉成 PR）
