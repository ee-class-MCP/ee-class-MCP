# 程式碼貢獻指南（Contributing Guide）

本指南適用於 `ee-class MCP` 專案團隊的開發與協作流程。送出 Pull Request（PR）前，請先確認已遵守以下規範。

> [!IMPORTANT]
> 本文檔為 Google Antigravity 協作產生初稿，並經由 Allen 審閱與修改。

*特別感謝 `ShiYu0318` 提供參考*

---

## 一、第一次貢獻與專案導覽

### 1. 快速流程
1. **確認或建立 Issue**：先搜尋既有 Issue，或依規範開立新 Issue 說明問題與預期成果（詳見[三、Issue 與團隊協作原則](#三issue-與團隊協作原則)）。
2. **認領任務與對齊介面**：在 Issue 中認領範圍明確的任務，並認領為負責人；若涉及跨組或共用介面修改，先在 Issue 或 Draft PR 對齊規格。
3. **建立環境並執行本地檢查**：依下方環境說明使用 `uv` 同步套件，並執行 `ruff` 與單元測試。**執行預設單元測試不需要真實的 ee-class 帳號密碼**。
4. **及早開立 Draft PR**：連結對應 Issue 並標註受影響模組，方便早期討論；完成所有檢查與說明後再轉為 Ready for review。
5. **回應審查意見並合併**：修正 Review 回饋並確認所有檢查通過後，交由指定人員合併。

### 2. Repo 結構導覽

| 領域 | 位置 | 主要職責 |
| --- | --- | --- |
| 認證與連線 | `src/eeclass_mcp/client/` | ee-class 登入驗證、Session、HTTP Client 與通訊協定封裝 |
| 資料模型 | `src/eeclass_mcp/models/` | 共用 Pydantic 資料模型與回傳結構定義 |
| HTML 解析 | `src/eeclass_mcp/parsers/` | 課程、公告、作業與教材頁面之 HTML 解析邏輯 |
| MCP Tools | `src/eeclass_mcp/tools/` | 對外暴露的 MCP tool 介面與參數處理 |
| Server 核心 | `src/eeclass_mcp/` | `server.py`、`config.py`、`app_context.py`、`logging_config.py` |
| 測試與樣本 | `tests/`、`tests/fixtures/` | 離線單元測試與去識別化後的 HTML fixture |
| 協作模板 | `.github/` | Issue 模板與 Pull Request 模板 |

> [!TIP]
> 本機暫存檔案（如 `.env`、`downloads/`、`.venv/`）、私人筆記或未去識別化的測試錄影與頁面快照，皆**不可**納入 Git 版本控制。

---

## 二、開發環境與相依管理

本專案要求 Python `>=3.14`，並統一使用 `uv` 管理虛擬環境與套件相依：

```bash
# 同步開發環境與相依套件
uv sync
```

- **lockfile 同步**：新增、移除或升級套件時，必須將 `pyproject.toml` 與 `uv.lock` 一併納入 PR，並在 PR description 中說明用途。
- **環境設定同步**：新增或調整環境變數時，請留存 `.env` 於本機並同步更新 `.env.example`（僅填寫範例佔位值，嚴禁放入真實帳號、密碼或個人端點）。

---

## 三、Issue 與團隊協作原則

- **Issue 先行與單一成果**：任何工作（功能開發、bug 修復、重構、測試或文件調整）皆應從 Issue 開始，每個 Issue 只對應一個範圍明確、可驗證的成果。若在開發或 Review 過程中發現其他問題，請另外開立新 Issue 追蹤，不把無關修改混進同一份 PR。
- **開立前先搜尋**：建立新 Issue 前請先搜尋 open 與 closed 的 Issue，若已有相同項目請直接於原 Issue 留言補充，避免重複開立。
- **標題描述「現況問題」**：Issue 標題應聚焦於「目前出現的問題或需求」，而非預設實作解法，並標示受影響的模組（例如 `[Bug]: parser fails on announcements without attachments`）。
- **內文與模板**：建立 TODO 任務時可使用專案既有的 [todo-模板.md](.github/ISSUE_TEMPLATE/todo-模板.md)。內文應清楚說明現況與完成標準，並僅使用假資料或去識別化後的資訊。
- **開工前先認領**：處理任務前，先將自己加入該 Issue 的 `Assignees`，並搭配小組或模組 Label 標示歸屬，避免兩個小組重複開發相同項目。
- **跨組介面先對齊**：若改動會影響另一小組或共用模組（例如共用資料 model、MCP tool schema、`client` 或 `parser` 介面），請先於 Issue 中討論或開啟 Draft PR 對齊介面規格，再進行實作。
- **安全性例外**：若發現尚未修復的安全漏洞（例如認證繞過、憑證洩漏風險），**請勿公開開立 Issue**，改以私下方式聯繫專案負責人（Allen 或 Steve）。

---

## 四、分支策略與 Git 流程

- **`main` 分支限制**：嚴禁直接 push 至 `main`，所有變更（含文件修改）一律透過 PR 合併。
- **從最新 `main` 建立分支**：每個 Issue 開立一個獨立分支，建議指令如下：

```bash
git switch main
git pull --ff-only
git switch -c feat/12-course-parser
```

- **分支命名規範**：統一採用 `<type>/<issue編號>-<簡短描述>` 格式，常用前綴為 `feat/`、`fix/`、`refactor/`、`docs/`、`test/`、`ci/`、`chore/`：
  - `feat/12-course-parser`
  - `fix/15-login-timeout`
  - `docs/20-contributing-guide`
- **單一職責與 Rebase 禮儀**：
  - 每個 PR 僅處理單一 Issue（或主題緊密相關的多個子任務），不可在功能性 PR 中混入無關的全專案格式重整。
  - 送出 PR 前請先同步最新 `main`（`rebase` 或 `merge`）並解決衝突；**僅限 rebase 自己獨自開發的分支**，勿在未協調的情況下改寫或強制推送他人共用的分支歷史。
- **合併策略**：統一採用 **Squash and merge**，使 `main` 分支的 commit 歷史能直接對應符合規範的 PR 標題。

---

## 五、Pull Request 規範

### 1. PR 標題格式：Conventional Commits

所有 PR 標題須遵守 Conventional Commits 規範，格式如下：

```text
<type>(<scope>): <description>
```

- `type` 一律使用英文（必填）；`scope` 為影響模組（選填）；`description` 中英文皆可（技術名詞與識別字保留原文），建議簡潔明確。
- 建議 `scope` 名稱：`client`、`auth`、`parsers`、`models`、`tools`、`server`、`config`、`tests`、`docs`、`ci`。
- 常用 `type` 說明：

| Type | 用途說明 |
| --- | --- |
| `feat` | 新增功能 |
| `fix` | 修復 bug |
| `docs` | 文件新增或修改 |
| `refactor` | 重構（不影響外部行為的新增或修復除外） |
| `test` | 新增或調整測試 |
| `chore` | 建置工具、相依套件或雜項維護 |
| `style` | 僅影響程式碼格式（不影響邏輯） |
| `perf` | 效能改善 |
| `ci` | CI/CD 或自動化工作流程調整 |

- **不相容變更（Breaking Change）**：若變更會破壞既有 MCP tool schema、回傳欄位或設定檔格式，請在 `type`／`scope` 後加上 `!`（例如 `feat(tools)!: rename course list output fields`），並於 PR description 中說明影響範圍與遷移方式。
- 正確範例：
  - `feat(parsers): 支援課程公告列表解析`
  - `fix(auth): handle expired session redirect`
  - `docs: 新增專案貢獻指南`

### 2. PR 模板、關聯 Issue 與審查範圍

- **使用 PR 模板**：所有 PR 皆須依照專案的 [pull_request_template.md](.github/pull_request_template.md) 填寫（開立 PR 時 GitHub 會自動載入），請勿刪除必要欄位。
- **關聯 Issue**：於 PR description 中使用關閉關鍵字明確標註對應的 Issue（完成時使用 `Closes #<編號>` 或 `Fixes #<編號>`，建議一行一個；僅涉及部分進度時使用 `Refs #<編號>`）。PR 中不應包含未被任何 Issue 描述到的工作。
- **Draft PR 原則**：Draft PR 僅供早期討論與對齊介面使用，不可直接合併；確認實作與說明皆完整後再切換為 Ready。
- **如實回報驗證狀態**：說明實際執行過的檢查項目；若有測試因本地環境限制未能執行（例如無法連線真實校內環境執行 `integration` 測試），須於 PR description 中明確註明。

---

## 六、AI 使用揭露與責任規範

- **強制揭露**：每個 PR 皆須於 PR description 中依程度勾選 AI 使用情形（未使用亦須勾選「未使用」）；若有使用 AI，須補填下列三項資訊（若已知工具或模型版本，建議一併註明）。
- **必填三項資訊**：
  1. **使用的軟體／工具**：明確寫出使用的 AI 工具或模型名稱（例如 Antigravity、Cursor、GitHub Copilot、Claude、ChatGPT 等）。
  2. **進行的操作**：說明 AI 協助的工作類型（例如生成初版程式、重構、撰寫單元測試、除錯查詢、整理文件等）。
  3. **影響範圍**：具體列出 AI 參與產出或修改的檔案、模組或函式範圍。
- **人類負最終責任原則**：提交者必須完全理解 PR 中的每一行程式碼，並親自完成本地測試與品質檢查。
- **禁止未經檢視之大量生成程式碼**：不可將未經人工閱讀、驗證與整理的大段 AI 生成程式碼直接送出請隊友 Review。
- **禁止捏造與機密邊界**：
  - 嚴禁偽造作者署名、測試通過紀錄、benchmark 數據或 Review 核准狀態。
  - 禁止將真實學號、密碼、Session Cookie 或未去識別化的學生頁面 HTML 傳送至未經授權的外部 AI 工具。

可在 PR description 中直接參考以下格式填寫：

````markdown
## AI 使用揭露
- [ ] **未使用**：本次變更完全未使用 AI 工具
- [ ] **輕度輔助**：僅用於查詢資料、除錯建議、命名或文件潤飾
- [x] **中度協作**：用於產生樣板程式碼、單元測試或局部重構
- [ ] **高度參與**：用於產出重要功能程式碼或跨檔案實作，且**已由本人逐行審核與驗證**

- **使用工具**：Antigravity / GitHub Copilot
- **進行操作**：生成單元測試草稿、協助除錯正規表示式
- **影響範圍**：`src/eeclass_mcp/parsers/announcement.py` (`parse_announcements`)、`tests/test_announcement_parser.py`
````

---

## 七、程式碼品質、測試與專案專屬規範

### 1. 提交前本地檢查

送出 PR 前，請先在本地執行並通過以下所有檢查（設定見 `pyproject.toml`）：

```bash
# Lint 檢查
uv run ruff check .

# 程式碼格式檢查（如需自動格式化可執行：uv run ruff format .）
uv run ruff format --check .

# 執行單元測試（預設排除 integration marker）
uv run pytest
```

### 2. 測試隔離與涵蓋原則

- **離線與隔離原則**：單元測試應使用 `respx` 模擬 HTTP 回應或使用去識別化後的 HTML fixture，**不得依賴開發者本機 `.env` 設定或真實外部帳號**。
- **整合測試標記**：涉及實際連線 NCU ee-class 網站的測試必須加上 `@pytest.mark.integration`（預設測試指令已依 `pyproject.toml` 排除），不可將依賴真實帳密或網路的測試加入預設單元測試組；送出 PR 時請一併說明手動驗證或整合測試的結果與限制。
- **回歸測試與例外**：新增功能或修復 bug 時應補齊對應的單元測試；僅修改文件（`docs`）的 PR 不需硬加無意義測試。

### 3. 模組邊界與程式碼整潔度

- **嚴守模組邊界**：
  - 登入驗證、Session 管理與 HTTP／Playwright 操作保留在 `src/eeclass_mcp/client/`；
  - HTML 解析邏輯保留在 `src/eeclass_mcp/parsers/`，並輸出 `src/eeclass_mcp/models/` 定義的 Pydantic 模型；
  - MCP tool 介面與參數驗證保留在 `src/eeclass_mcp/tools/`，勿將爬蟲解析細節寫入 tool handler。
- **公開介面相容性**：除非 PR 明確說明相容性變更，否則應保留既有 MCP tool 名稱、輸入參數與公開 model 欄位結構。
- **註解與程式碼清理**：註解應說明**為什麼**存在非直覺的限制（例如 ee-class 網頁的特殊 DOM 結構或登入重導向行為）。提交前請移除過時的規劃註記、被註解掉的實驗程式碼，以及僅在重述程式碼動作的旁白註解。

### 4. MCP `stdio` 輸出規範

- 本專案的 MCP server 透過 `stdio` 傳輸協定訊息，正式程式碼**禁止使用 `print()`** 寫入 `stdout`。
- 所有除錯訊息與執行日誌一律透過標準 `logging` 模組輸出至 `stderr`。

---

## 八、安全與隱私規範

- **嚴禁提交憑證**：本地開發請參考 `.env.example` 建立 `.env`；**切勿將 `.env`、真實學號、密碼、Session Cookie 或認證 Token** 加入版本控制。
- **測試資料去識別化**：提交測試用 HTML fixture、執行 log 或截圖至 repo、Issue 或 PR 前，**務必移除個人姓名、學號、信箱、成績與 Session** 等敏感資訊。
- **漏洞回報原則**：未修復之安全漏洞請私下聯繫專案負責人處理，勿直接公開於 Issue 或 PR 討論串。

---

## 九、Code Review 與合併流程

- **審查門檻**：PR 須獲得 **Allen 或 Steve 其中一位** Approve 才可合併。
- **合併權限與方式**：通過審查（且討論皆已解決、相關檢查完成、Draft 已轉為 Ready）後，由 **Reviewer 或指定負責人** 以 **Squash and merge** 執行合併；PR 作者**不可**在未達審查門檻時自行合併，Draft PR 亦不可合併。
- **審查時效**：收到 Review 通知後建議盡快回覆審查意見，避免阻塞其他成員或另一小組的開發進度。
