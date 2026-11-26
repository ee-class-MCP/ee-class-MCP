# 程式碼貢獻指南（Contributing Guide）

本指南適用於 `ee-class MCP` 專案團隊的開發與協作流程。送出 Pull Request（PR）前，請先確認已遵守以下規範。

> [!NOTE]
> 本文檔為 Google Antigravity 協作產生初稿，並經由 Allen 審閱與修改。 

---

## 一、Issue 與團隊協作原則

- **優先處理 Issue**：各組成員應優先處理 GitHub Issues 上列出的階段性任務與待辦事項；建立 TODO 任務時可使用專案既有的 [todo-模板.md](.github/ISSUE_TEMPLATE/todo-模板.md)。
- **開工前先認領**：處理任務前，先將自己加入該 Issue 的 `Assignees`，並搭配小組或模組 Label 標示歸屬，避免兩個小組重複開發相同項目。
- **跨組介面先對齊**：若改動會影響另一小組或共用模組（例如共用資料 model、MCP tool schema、client 或 parser 介面），請先於 Issue 中討論或開啟 Draft PR 對齊介面規格，再進行實作。

---

## 二、開發環境與相依管理

本專案要求 Python `>=3.14`，並統一使用 `uv` 管理虛擬環境與套件相依：

```bash
# 同步開發環境與相依套件
uv sync
```

- 新增、移除或升級套件時，必須將 `pyproject.toml` 與 `uv.lock` 一併納入 PR，並在 PR description 中說明用途。

---

## 三、分支策略與 Git 流程

- **`main` 分支限制**：嚴禁直接 push 至 `main`，所有變更（含文件修改）一律透過 PR 合併。
- **分支命名規範**：統一採用 `<type>/<issue編號>-<簡短描述>` 格式：
  - `feat/12-course-parser`
  - `fix/15-login-timeout`
  - `docs/20-contributing-guide`
- **單一職責與保持同步**：每個 PR 僅處理單一 Issue 或明確的子任務；送出 PR 前，請先同步最新 `main`（`rebase` 或 `merge`）並解決衝突。
- **合併策略**：統一採用 **Squash and merge**，使 `main` 分支的 commit 歷史能直接對應符合規範的 PR 標題。

---

## 四、Pull Request 規範

### 1. PR 標題格式：Conventional Commits

所有 PR 標題須遵守 Conventional Commits 規範，格式如下：

```text
<type>(<scope>): <description>
```

- `type` 一律使用英文（必填）；`scope` 為影響模組（選填）；`description` 中英文皆可，建議簡潔明確。
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

- 正確範例：
  - `feat(parser): 支援課程公告列表解析`
  - `fix(auth): handle expired session redirect`
  - `docs: 新增專案貢獻指南`

### 2. PR 模板與關聯 Issue

- **使用 PR 模板**：所有 PR 皆須依照專案的 [pull_request_template.md](.github/pull_request_template.md) 填寫（開立 PR 時 GitHub 會自動載入），請勿刪除必要欄位。
- **關聯 Issue**：於 PR description 中明確標註對應的 Issue（完成時使用 `Closes #<編號>` 或 `Fixes #<編號>`；僅涉及部分進度時使用 `Refs #<編號>`）。

---

## 五、AI 使用揭露與責任規範

- **強制揭露**：每個 PR 皆須於 PR description 中依程度勾選 AI 使用情形（未使用亦須勾選「未使用」）；若有使用 AI，須補填下列三項資訊。
- **必填三項資訊**：
  1. **使用的軟體／工具**：明確寫出使用的 AI 工具或模型名稱（例如 Antigravity、Cursor、GitHub Copilot、Claude、ChatGPT 等）。
  2. **進行的操作**：說明 AI 協助的工作類型（例如生成初版程式、重構、撰寫單元測試、除錯查詢、整理文件等）。
  3. **影響範圍**：具體列出 AI 參與產出或修改的檔案、模組或函式範圍。
- **人類負最終責任原則**：提交者必須完全理解 PR 中的每一行程式碼，並親自完成本地測試與品質檢查。
- **禁止未經檢視之大量生成程式碼**：不可將未經人工閱讀、驗證與整理的大段 AI 生成程式碼直接送出請隊友 Review。

可在 PR description 中直接參考以下格式填寫：

````markdown
## AI 使用揭露
- [ ] **未使用**：本次變更完全未使用 AI 工具
- [ ] **輕度輔助**：僅用於查詢資料、除錯建議、命名或文件潤飾
- [x] **中度協作**：用於產生樣板程式碼、單元測試或局部重構
- [ ] **高度參與**：用於產出重要功能程式碼或跨檔案實作，且**已由本人逐行審核與驗證**

- **使用工具**：Antigravity / GitHub Copilot
- **進行操作**：生成單元測試草稿、協助除錯正規表示式
- **影響範圍**：`src/eeclass_mcp/parser.py`（`parse_announcements`）、`tests/test_parser.py`
````

---

## 六、程式碼品質、測試與專案專屬規範

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

- 若變更涉及實際網站連線行為，請在 PR 中說明手動測試或整合測試（`integration`）的驗證方式與結果。
- 新增功能或修復 bug 時，應一併補齊對應的單元測試（例如使用 `respx` 模擬 HTTP 回應或使用去識別化後的 HTML fixture）。

### 2. MCP `stdio` 輸出規範

- 本專案的 MCP server 透過 `stdio` 傳輸協定訊息，正式程式碼**禁止使用 `print()`** 寫入 `stdout`。
- 所有除錯訊息與執行日誌一律透過標準 `logging` 模組輸出至 `stderr`。

---

## 七、安全與隱私規範

- **嚴禁提交憑證**：本地開發請參考 `.env.example` 建立 `.env`；**切勿將 `.env`、真實學號、密碼、Session Cookie 或認證 Token** 加入版本控制。
- **測試資料去識別化**：提交測試用 HTML fixture、執行 log 或截圖至 repo、Issue 或 PR 前，**務必移除個人姓名、學號、信箱、成績與 Session** 等敏感資訊。

---

## 八、Code Review 與合併流程

- **審查門檻**：PR 至少須獲得 **2 位成員 Approve** 才可合併。
- **合併權限與方式**：通過審查後，由 **Reviewer 或指定負責人** 以 **Squash and merge** 執行合併；PR 作者**不可**在未達審查門檻時自行合併。
- **審查時效**：收到 Review 通知後建議盡快回覆審查意見，避免阻塞其他成員或另一小組的開發進度。
