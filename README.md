# 📱 Superb LINE Bot 精湛教育課務小幫手

A production-grade LINE chatbot used by **Superb Education** for streamlining daily teaching operations.

這是一個實際應用於「精湛教育」的 LINE 聊天機器人，專為補教課務管理設計。老師透過 LINE 就能完成打卡、記錄學生作業與進度、通知下次上課時間，並自動同步 Google 試算表，提升行政效率與教學體驗。

---

## ✨ Features | 主要功能

- ✅ **Teacher check-in/out**  
  老師上下課打卡，自動記錄時間並計算授課時數

- 📝 **Progress & homework recording**  
  課堂進度與作業記錄功能，完整保留教學軌跡

- 📅 **Class scheduling reminders**  
  一鍵通知家長／學生下次上課時間，減少溝通負擔

- 🧾 **Google Sheets integration**  
  所有資料即時同步到雲端試算表，便於行政統計與報表匯出

- 🔐 **User identity state tracking**  
  管理老師、學生、群組設定狀態，讓機器人對話更具彈性與上下文

---

## 🔧 Tech Stack | 技術架構

- Python + Flask
- LINE Messaging API
- Google Sheets API (`pygsheets`)
- Heroku (deployment)

---

## 📌 Repository Highlights

- `get_sheet()` / `add_row_data()` / `update_cell_data()` – Google Sheets 操作封裝
- `get_teacherState()` / `update_teacherInfo()` – 老師帳號管理邏輯
- `add_startTime()` / `add_endTime()` – 課程打卡與時數計算
- `getFlexTimeMessageF()` – Flex Message 卡片顯示課程摘要
- Webhook handler for LINE message + postback events

---

## 🏫 About Superb Education

**Superb Education** 是一間致力於個別化教學的教學品牌，本專案為其內部課務管理自動化工具之一，由學生自主開發並實際部署使用中。

---

📬 Maintained by [Pierre Chen](https://github.com/ntupierre) | NTU Information Management
