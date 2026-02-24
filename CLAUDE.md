# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A LINE chatbot for **Superb Education** (精湛教育) that manages tutoring operations: teacher check-in/out, progress/homework recording, next-class scheduling, and group setup. All data is persisted to Google Sheets.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (requires env vars and Superb_IAM_admin.json)
python app.py
```

## Deployment (Zeabur)

Zeabur 透過 `Procfile` 啟動（`web: python app.py`）。部署流程：
1. 將 repo 連接到 Zeabur 專案
2. 在 Zeabur Dashboard → Environment Variables 設定以下變數
3. Redeploy

## Required Environment Variables

- `LINE_CHANNEL_ACCESS_TOKEN` — LINE Messaging API token
- `LINE_CHANNEL_SECRET` — LINE webhook secret
- `GOOGLE_SERVICE_ACCOUNT_JSON` — `Superb_IAM_admin.json` 的完整 JSON 內容（貼上整個檔案的文字）
- `SPREADSHEET_ID` — Google 試算表 ID（網址 `/d/` 後面那串）

## Required Files (gitignored, 本地開發用)

- `Superb_IAM_admin.json` — 本地開發時使用的 Google Service Account 憑證；若環境變數 `GOOGLE_SERVICE_ACCOUNT_JSON` 存在則優先使用環境變數

## Architecture

Everything lives in `app.py` (single file). Flask serves a `/callback` POST endpoint that LINE calls as a webhook.

### Google Sheets as Database

Four worksheets are used (spreadsheet IDs are hardcoded as `'google.location'` — placeholders that need real IDs):

| Sheet | Columns | Purpose |
|---|---|---|
| `teacherInfo` | userId, state, name | Teacher registration & state |
| `groupInfo` | groupId, state, respTeacher, name, teacher, teacherPay, cost | Group/student setup |
| `dataForthisMonth` | date, startTime, teacher, studentName, endTime, duration, progress, homework | Class session records |
| `forTest` | — | Testing |

### State Machine Pattern

State is stored in Google Sheets columns, not in memory. The bot reads state on every message to decide how to respond.

**Teacher states** (`teacherInfo.state`):
- `noData` → not registered
- `adding` → waiting for teacher name input
- `normal` → fully registered, can use all features
- `addingProgress` → waiting for progress text input
- `addingHomework` → waiting for homework text input

**Group states** (`groupInfo.state`):
- `addingStudent` → waiting for student name
- `addingTeacher` → waiting for teacher name
- `normal` → fully configured

### Event Handlers

- `handle_message(event)` — handles `TextMessage` events; a large if/elif chain dispatching on `message_text` and current state from Sheets
- `handle_postback(events)` — handles `PostbackEvent` from datetime pickers; dispatches on `events.postback.data` values: `'資料上課'` (check-in), `'資料下課'` (check-out), `'下次上課時間'` (next class notification)

### Key Flows

1. **Teacher registration**: `登錄老師名字` → `add_teacherInfo()` sets state=`adding` → next text sets name, state=`normal`
2. **Check-in**: datetime picker → postback `資料上課` → `add_startTime()` writes date/time/teacher/student to `dataForthisMonth`
3. **Check-out**: postback `資料下課` → `find_endTimeRow()` locates the open row → `add_endTime()` writes end time + spreadsheet formula for duration → sends Flex Message summary
4. **Progress/homework**: `登記本次進度作業` → state=`addingProgress` → text → state=`addingHomework` → text → state=`normal`
5. **Group setup**: `設定群組學生資訊` → `add_groupInfo()` → state=`addingStudent` → student name → state=`addingTeacher` → teacher name → state=`normal`

### Flex Messages

Three builder functions return `FlexSendMessage` objects:
- `getFlexTimeMessageF()` — class summary card (time only, no progress/homework yet)
- `getFlexTimeMessageF2()` — class summary card with progress and homework
- `getFlexNextTimeMessageF()` — next class notification card

### Time Zone Handling

The server runs in UTC; `timedelta(hours=8)` is added to convert to Taiwan time (UTC+8) when building datetime picker `initial` values. Postback datetimes from LINE are already in local time as selected by the user.
