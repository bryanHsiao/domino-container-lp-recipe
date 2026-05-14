# The "Data Already Installed" Sync Trap / 「Data Already Installed」同步陷阱

> The most important caveat when adding LP support to an already-running Domino server. Read this **before** rebuilding your image with this recipe.
>
> 對「已運行的 Domino server」加 LP 支援時最重要的注意事項。**重 build image 之前**請讀。

---

## English

### Symptom

You successfully:
1. Ran this recipe to integrate TC (or another LP)
2. Rebuilt the image with `./build.sh ... -domlp=TC`
3. Verified the image contains TC resources (`verify.sh --lang TC` passes)
4. Restarted your `domino-lab` container with the new image

…but when you log into Notes Client, **the UI is still English**:
- `names.nsf` views (`People`, `Groups`, `Configuration`) — English
- Any existing `mail/*.nsf` files — English
- A newly-created `testmail.nsf` (from server template) — also **English**

This is **not** a build failure. The image really does contain Traditional Chinese templates. But they're not being used.

### Root cause

Domino container's entrypoint checks `/local/notesdata` at startup. If it finds an existing installation, it skips template deployment:

```
DOMINO_VERSION: [14050100]
INSTALLED_VERSION: [14050100]
Data already installed for 14050100        ← the killer line
Data already installed for leap 1.1.10
```

So:

| Scenario | Result |
|---|---|
| `/local/notesdata` empty (first-time setup) | Entrypoint extracts templates from image's `install_data_domino.taz` → LP-aware templates land in data dir → all newly-created DBs use the new templates → ✅ |
| `/local/notesdata` already has 14.5.1 data (you set up before adding LP) | Entrypoint says "already installed" → **skips template deployment entirely** → `mail145.ntf` / `pubnames.ntf` / etc. stay as the old (English) versions → ❌ |

The companion `HCL Issue #55` thread captured this exactly: maintainer said "no concept adding any data after initial configuration." This is that limitation in practice.

### Solution (lab environment) — fresh OneTouch Setup

If your data dir contents are disposable, do a fresh setup:

```bash
# 1. Stop & remove the container
dominoctl stop
docker rm domino-lab

# 2. Back up existing data dir (mv, not rm — keep for rollback)
mv /local/notesdata /local/notesdata.bak-en-$(date +%s)

# 3. Create empty data dir (UID 1000 — required, see your container's docs)
mkdir /local/notesdata
chown 1000:1000 /local/notesdata

# 4. Confirm your OneTouch JSON is in place
ls -la /etc/sysconfig/DominoContainerAutoConfig.json{,.bak} 2>/dev/null
# If only .bak exists (dominoctl renames it after first successful setup):
#   cp /etc/sysconfig/DominoContainerAutoConfig.json.bak /etc/sysconfig/DominoContainerAutoConfig.json
# If the JSON content was overwritten with defaults (Acme / John Doe):
#   patch it back using jq — see your Domino setup notes

# 5. Start fresh — server detects "empty data dir" → runs OneTouch automatically (3–5 min)
dominoctl start
sleep 60
dominoctl status
```

### Verifying the LP actually took effect

Two independent checks:

```bash
# (a) New mail145.ntf md5 should differ from the backup
docker exec domino-lab md5sum /local/notesdata/mail145.ntf
md5sum /local/notesdata.bak-en-*/mail145.ntf
# Expected: DIFFERENT — confirms LP templates came from the image, not from old data

# (b) Server console.log should contain target-language strings
docker exec domino-lab grep -a "網域監督\|事件\|郵件\|目錄" \
  /local/notesdata/IBM_TECHNICAL_SUPPORT/console.log | head -5
# Expected: Chinese strings appear (e.g. "網域監督" = "Domain Monitoring")
# This is server-side output, not Notes Client UI — direct proof LP is active.
```

### Notes Client ID mismatch (follow-on issue)

Fresh setup generates a **new `admin.id`** whose public key differs from your old Notes Client's. Notes Client authentication will fail:

```
Admin/TheNet from host [127.0.0.1] failed to authenticate:
The subject's public key found in the certificate is not the one stored in our ID file for that entity.
```

Fix: copy the new admin.id out of the container, replace the one in Notes Client:

```bash
docker cp domino-lab:/local/notesdata/admin.id /mnt/c/Users/<USER>/Downloads/admin-new.id
```

Then in Notes Client: **File → Security → Switch ID → 選 admin-new.id**.

### Production environment — don't do the fresh-setup trick

For production servers, dropping `/local/notesdata` is unacceptable. Instead:

1. **Replace Design** each affected `.nsf` from Notes Admin client (or `load convert -r <db> <template>` from server console), targeting the new templates in `/local/notesdata`
2. The new templates exist in data dir because… well, they don't yet — fresh setup is the only mechanism that deploys them currently
3. So in production: you may need to either accept that existing DBs stay English (and only new DBs are localized), or manually `docker cp` the new templates out of a fresh test container and place them in production's data dir, then Replace Design

This is genuinely awkward — it's the gap @Daniel-Nashed described in HCL Issue #55. A proper production-grade story would need either:
- Upstream changes (e.g. a Domino server task that re-deploys templates from a release archive)
- Or a HCL-blessed migration procedure (none currently exists in the container's documentation)

This recipe does not solve production migration. It solves "I'm setting up a new server and want LP from day 1" cleanly.

---

## 繁體中文

### 症狀

你成功完成：
1. 用本工具整合 TC（或其他 LP）
2. 用 `./build.sh ... -domlp=TC` 重 build image
3. 用 `verify.sh --lang TC` 驗證 image 含 TC 資源（通過）
4. 用新 image 重啟 `domino-lab` container

…但用 Notes Client 登入後，**介面仍是英文**：
- `names.nsf` 內的檢視畫面（`People`、`Groups`、`Configuration`） — 英文
- 既有的 `mail/*.nsf` — 英文
- 新建的 `testmail.nsf`（從 server 取範本） — **也是英文**

這 **不是** build 失敗。Image 內確實含繁中範本。但它們沒被用到。

### 根因

Domino container 的進入點啟動時會檢查 `/local/notesdata`。如果偵測到既有安裝，就跳過範本部署：

```
DOMINO_VERSION: [14050100]
INSTALLED_VERSION: [14050100]
Data already installed for 14050100        ← 關鍵這行
Data already installed for leap 1.1.10
```

所以：

| 情境 | 結果 |
|---|---|
| `/local/notesdata` 空的（第一次 setup）| 進入點從 image 內的 `install_data_domino.taz` 解出範本 → 帶 LP 的範本進入資料目錄 → 新建的 DB 都用新範本 → ✅ |
| `/local/notesdata` 已有 14.5.1 資料（你加 LP 之前已經 setup 過）| 進入點說「already installed」→ **完全跳過範本部署** → `mail145.ntf`、`pubnames.ntf` 等保持舊（英文）版 → ❌ |

對應 `HCL Issue #55` 討論串中維護者說的：「no concept adding any data after initial configuration.」這就是那個限制的實際樣子。

### 解法（lab 環境）— 重做 OneTouch Setup

如果資料目錄內容可以丟，重做 setup：

```bash
# 1. 停止並移除 container
dominoctl stop
docker rm domino-lab

# 2. 備份既有資料目錄（mv，不是 rm — 保留作回滾保險）
mv /local/notesdata /local/notesdata.bak-en-$(date +%s)

# 3. 建立空的資料目錄（UID 1000 — 必須，見你 container 的文件）
mkdir /local/notesdata
chown 1000:1000 /local/notesdata

# 4. 確認 OneTouch JSON 在位
ls -la /etc/sysconfig/DominoContainerAutoConfig.json{,.bak} 2>/dev/null
# 如果只有 .bak 存在（dominoctl 第一次 setup 完會自動改名）：
#   cp /etc/sysconfig/DominoContainerAutoConfig.json.bak /etc/sysconfig/DominoContainerAutoConfig.json
# 如果 JSON 內容被覆蓋成預設值（Acme / John Doe）：
#   用 jq 改回你要的設定 — 見你 Domino 設定筆記

# 5. 啟動 — server 偵測「空的資料目錄」會自動跑 OneTouch（3–5 分鐘）
dominoctl start
sleep 60
dominoctl status
```

### 驗證 LP 真的生效

兩個獨立檢查：

```bash
# (a) 新的 mail145.ntf 的 md5 應該跟備份不同
docker exec domino-lab md5sum /local/notesdata/mail145.ntf
md5sum /local/notesdata.bak-en-*/mail145.ntf
# 預期：兩個不同 — 證實新範本是從 image 來，不是舊資料

# (b) Server console.log 應該含目標語言字串
docker exec domino-lab grep -a "網域監督\|事件\|郵件\|目錄" \
  /local/notesdata/IBM_TECHNICAL_SUPPORT/console.log | head -5
# 預期：看到繁中字串（例如「網域監督」= Domain Monitoring）
# 這是 server 端輸出、不是 Notes Client 介面 — LP 真的生效的直接證據
```

### Notes Client ID 不匹配（後續問題）

重做 setup 會產生**新的 `admin.id`**，公鑰跟你 Notes Client 內舊的不同。Notes Client 認證會失敗：

```
Admin/TheNet from host [127.0.0.1] failed to authenticate:
The subject's public key found in the certificate is not the one stored in our ID file for that entity.
```

修法：把 container 內的新 `admin.id` 撈出來，取代 Notes Client 內舊的：

```bash
docker cp domino-lab:/local/notesdata/admin.id /mnt/c/Users/<USER>/Downloads/admin-new.id
```

然後在 Notes Client：**File → Security → Switch ID → 選 admin-new.id**。

### 正式環境 — 不能用「重做 setup」這招

對正式環境的 server，丟掉 `/local/notesdata` 不可接受。取而代之的做法：

1. 對每個受影響的 `.nsf`，從 Notes Admin 端做 **Replace Design**（或從 server console 執行 `load convert -r <db> <template>`），目標是 `/local/notesdata` 內的新範本
2. 但資料目錄內**沒有新範本** — 重做 setup 是目前唯一會部署它們的機制
3. 所以正式環境的選擇：要嘛接受既有 DB 保持英文（只有新建 DB 是本地化的），要嘛從乾淨的測試 container 手動 `docker cp` 新範本出來、放進正式環境的資料目錄、再做 Replace Design

這真的很彆扭 — 就是 @Daniel-Nashed 在 HCL Issue #55 描述的缺口。完整的正式環境解法需要：
- 上游改動（例如 Domino server 提供 task 從 release archive 重新部署範本）
- 或 HCL 官方認可的遷移程序（目前 container 文件內沒有）

本工具**不解決**正式環境的遷移問題。它解決的是「我在建新 server，希望 LP 從第一天就在」這個情境。
