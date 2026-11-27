# 測試用靜態 HTML

2026-11-26 從 `https://ncueeclass.ncu.edu.tw` 抓取的伺服器原始回應（未執行 JavaScript，和 `httpx` 拿到的一致）。
檔名依 `scripts/capture_fixtures.py`（#9）的規則，由網址路徑產生。

| 檔案 | 路徑 | 內容 |
|---|---|---|
| `dashboard_latestEvent.html` | `/dashboard/latestEvent` | 近期事件（作業與期限） |
| `dashboard_latestBulletin.html` | `/dashboard/latestBulletin` | 最新公告 |
| `course_40286.html` | `/course/40286` | 課程首頁 |
| `course_material_40286.html` | `/course/material/40286` | 教材列表 |
| `media_doc_257408.html` | `/media/doc/257408` | 單一教材頁（多個附件） |
| `course_bulletin_40286.html` | `/course/bulletin/40286` | 課程公告列表 |
| `bulletin_content.html` | `/bulletin/content/?id=…` | 單一公告內容（公告列表的 `data-url`） |
| `course_homeworkList_40286.html` | `/course/homeworkList/40286` | 作業列表 |
| `course_homeworkList_42511.html` | `/course/homeworkList/42511` | 作業列表（沒有資料） |
| `course_homework_72152.html` | `/course/homework/72152` | 單一作業頁 |
| `course_homework_75575.html` | `/course/homework/75575` | 單一作業頁 |

首頁 `dashboard.html`（`/dashboard`）由 #9 提供，這裡不重複放。
它和上面的檔案來自不同帳號，所以兩邊的課程清單不一定相同。

## 寫解析器時注意

- `/course/homeworkList/{課程代號}` 是實際存在的作業列表網址。
- 原始 HTML 的屬性多用單引號。
- 公告列表的連結是 `href='####'`，真正的網址在 `data-url`。

## 已替換的內容

只換內容，標籤與 class 未更動。

| 原內容 | 替換值 |
|---|---|
| 姓名 | `使用者NN` |
| 學號、手機 | `100000000`、`0900000000` |
| email | `redacted@example.com` |
| `userId` / `poster` / `ouid` | `0` |
| `ajaxAuth`、`auth`、`anticsrf` | `REDACTED` |
| `/download/`、`/sysdata/` 路徑中的雜湊碼 | `0000000000000000` |
| 外部連結 | `https://example.com/link` |
| 等級與積分 | `0` |

公告標題、公告內文與作業說明已換成假文字（`測試公告 NN`、`測試公告內文 N`、`測試作業說明 N`）。
課程名稱、作業名稱與教材名稱保留原文。
