from flask import Flask, request, abort


from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

import pygsheets
from datetime import datetime, timedelta

import os
import json

# 設定 Google API 認證
def authenticate_google():
    google_creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if google_creds_json:
        # Vercel：從環境變數讀取 Google Service Account JSON 內容
        from google.oauth2.service_account import Credentials
        service_account_info = json.loads(google_creds_json)
        scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        client = pygsheets.authorize(custom_credentials=creds)
    else:
        # 本地開發：使用 JSON 檔案
        client = pygsheets.authorize(service_file='Superb_IAM_admin.json')
    return client

# 取得 Google 試算表
def get_sheet(spreadsheet_id, sheet_name):
    client = authenticate_google()
    spreadsheet = client.open_by_key(spreadsheet_id)
    sheet = spreadsheet.worksheet_by_title(sheet_name)
    return sheet

# 在試算表中新增一行資料
def add_row_data(sheet, row_data):
    sheet.append_table(values=row_data, dimension='ROWS', overwrite=False)

# 更新試算表中的特定儲存格資料
def update_cell_data(sheet, row, col, value):
    sheet.update_value((row, col), value)

# 設定試算表和工作表資訊
SPREADSHEET_ID = ""  # 試算表 ID
SHEET_NAME = ""  # 工作表名稱

# 取得試算表和工作表
sheet_forTest = get_sheet('google.location', 'forTest')

# 例如，新增一行資料
# row_data = ["資料1", "資料2", "資料3"]
# add_row_data(sheet_forTest, row_data)

# 例如，更新特定儲存格的資料
# row = 5
# col = 6
# value = "更新"

# 設定teacherInfo試算表和工作表資訊(Id,state,name)
sheet_teacherInfo = get_sheet('google.location', 'teacherInfo')

# 當有人點擊登記老師按鈕時，新增一行資料，並將state設為adding
def add_teacherInfo(userId):
    if get_teacherState(userId) == 'noData':
        adding_data = [userId, 'adding']
        add_row_data(sheet_teacherInfo, adding_data)

# 收到訊息時，回傳userId的state
def get_teacherState(userId):
    # 使用 get_col() 獲取整個欄位資料，不包括非零後的空白格
    userId_list = sheet_teacherInfo.get_col(1, include_tailing_empty=False)
    state_list = sheet_teacherInfo.get_col(2, include_tailing_empty=False)
    # 檢查 userId 是否在欄位資料中
    if userId in userId_list:
        # 取得相應的 state
        index = userId_list.index(userId)
        return state_list[index]
    else:
        return 'noData'
        
# 收到訊息時，回傳userId的name
def get_teacherName(userId):
    # 使用 get_col() 獲取整個欄位資料，不包括非零後的空白格
    userId_list = sheet_teacherInfo.get_col(1, include_tailing_empty=False)
    name_list = sheet_teacherInfo.get_col(3, include_tailing_empty=False)
    
    # 檢查 userId 是否在欄位資料中
    if userId in userId_list:
        # 取得相應的 name
        index = userId_list.index(userId)
        return name_list[index]
    else:
        return 'noData'
    
# 收到老師名字時，更新state為normal，並將name設為老師
def update_teacherInfo(teacherId, name):
    # 使用 get_col() 獲取整個欄位資料
    teacherId_list = sheet_teacherInfo.get_col(1, include_tailing_empty=False)
    # 檢查 teacherId 是否在欄位資料中
    if teacherId in teacherId_list:
        index = teacherId_list.index(teacherId) + 1  # 因為 get_col() 返回的列表是 0-based，所以要 +1 才是試算表中的行數
        update_cell_data(sheet_teacherInfo, index, 2, 'normal')  # 更新 state
        update_cell_data(sheet_teacherInfo, index, 3, name)  # 更新 name
    else:
        return 'Error'
    
# 更新老師狀態
def update_teacherState(teacherId, state):
    # 使用 get_col() 獲取整個欄位資料
    teacherId_list = sheet_teacherInfo.get_col(1, include_tailing_empty=False)
    # 檢查 teacherId 是否在欄位資料中
    if teacherId in teacherId_list:
        index = teacherId_list.index(teacherId) + 1  # 因為 get_col() 返回的列表是 0-based，所以要 +1 才是試算表中的行數
        update_cell_data(sheet_teacherInfo, index, 2, state)  # 更新 state
    else:
        return 'Error'
        
# 設定groupInfo試算表和工作表資訊(groupId, state, respTeacher, name, teacher, teacherPay, cost)
sheet_groupInfo = get_sheet('google.location', 'groupInfo')

# 當有人點擊設定群組學生資訊按鈕時，新增一行資料
def add_groupInfo(groupId, respTeacherId):
    respTName = get_teacherName(respTeacherId)
    adding_data = [groupId, 'addingStudent', respTName]
    add_row_data(sheet_groupInfo, adding_data)

# 收到訊息時，回傳userId的state
def get_groupState(groupId):
    # 使用 get_col() 獲取整個欄位資料，不包括非零後的空白格
    groupId_list = sheet_groupInfo.get_col(1, include_tailing_empty=False)
    state_list = sheet_groupInfo.get_col(2, include_tailing_empty=False)
    
    # 檢查 groupId 是否在欄位資料中
    if groupId in groupId_list:
        # 取得相應的 state
        index = groupId_list.index(groupId)
        return state_list[index]
    else:
        return 'noData'
        
# 收到訊息時，回傳userId的state
def get_groupName(groupId):
    # 使用 get_col() 獲取整個欄位資料，不包括非零後的空白格
    groupId_list = sheet_groupInfo.get_col(1, include_tailing_empty=False)
    name_list = sheet_groupInfo.get_col(4, include_tailing_empty=False)
    
    # 檢查 groupId 是否在欄位資料中
    if groupId in groupId_list:
        # 取得相應的 name
        index = groupId_list.index(groupId)
        return name_list[index]
    else:
        return 'noData'
        
# 收到學生名字時，更新state為addingTeacher，並將name設為學生
def update_groupInfoStudent(groupId, name):
    # 使用 get_col() 獲取整個欄位資料
    groupId_list = sheet_groupInfo.get_col(1, include_tailing_empty=False)
    
    # 檢查 groupId 是否在欄位資料中
    if groupId in groupId_list:
        index = groupId_list.index(groupId) + 1  # 因為 get_col() 返回的列表是 0-based，所以要 +1 才是試算表中的行數
        update_cell_data(sheet_groupInfo, index, 2, 'addingTeacher')  # 更新 state
        update_cell_data(sheet_groupInfo, index, 4, name)  # 更新 student name
    else:
        return 'Error'
        
# 收到老師名字時，更新state為normal
def update_groupInfoTeacher(groupId, name):
    # 使用 get_col() 獲取整個欄位資料
    groupId_list = sheet_groupInfo.get_col(1, include_tailing_empty=False)
    
    # 檢查 groupId 是否在欄位資料中
    if groupId in groupId_list:
        index = groupId_list.index(groupId) + 1  # 因為 get_col() 返回的列表是 0-based，所以要 +1 才是試算表中的行數
        update_cell_data(sheet_groupInfo, index, 2, 'normal')  # 更新 state
        update_cell_data(sheet_groupInfo, index, 5, name)  # 更新 teacher name
    else:
        return 'Error'

#登記打卡上課時間
sheet_dataForthisMonth = get_sheet('google.location', 'dataForthisMonth')

# 當有打卡上課時，新增上課資訊
def add_startTime(userId, groupId, message_dateTime):
    dateStr = message_dateTime.strftime('%Y-%m-%d')
    startTimeStr = message_dateTime.strftime('%H:%M')
    teachername = get_teacherName(userId)
    name = get_groupName(groupId)
    adding_data = [dateStr, startTimeStr, teachername, name]
    add_row_data(sheet_dataForthisMonth, adding_data)

# 當有打卡下課時，新增下課資訊
def add_endTime(endTimeRow, message_dateTime):
    endTimeStr = message_dateTime.strftime('%H:%M')
    calculateStr = '=E'+str(endTimeRow)+'-B'+str(endTimeRow)
    update_cell_data(sheet_dataForthisMonth, endTimeRow, 5, endTimeStr)
    update_cell_data(sheet_dataForthisMonth, endTimeRow, 6, calculateStr)

# find the end time row
def find_endTimeRow(userId, message_dateTime):
    # 轉換日期和教師名稱
    dateStr = message_dateTime.strftime('%Y-%m-%d')
    teachername = get_teacherName(userId)
    # 一次性獲取所有需要的資料列
    date_list = sheet_dataForthisMonth.get_col(1, include_tailing_empty=True)  # 確保不跳過空白值
    teacher_list = sheet_dataForthisMonth.get_col(3, include_tailing_empty=True)
    end_time_list = sheet_dataForthisMonth.get_col(5, include_tailing_empty=True)
    # 確認三個欄位的長度一致
    max_length = max(len(date_list), len(teacher_list), len(end_time_list))
    # 遍歷資料列，使用索引進行比對
    for i in range(max_length):
        if date_list[i] == dateStr and teacher_list[i] == teachername and end_time_list[i] == '':
            return i + 1  # 返回符合條件的行號，因為 get_col() 返回的索引是 0-based，所以這裡要加 1
    return 'Error'  # 如果找不到符合條件的行，返回 'Error'

# find the classing row
def find_classingRow(userId):
    # 轉換教師名稱
    teachername = get_teacherName(userId)
    # 一次性獲取所有需要的資料列
    teacher_list = sheet_dataForthisMonth.get_col(3, include_tailing_empty=True)
    end_time_list = sheet_dataForthisMonth.get_col(5, include_tailing_empty=True)
    # 確認三個欄位的長度一致
    max_length = max(len(teacher_list), len(end_time_list))
    # 遍歷資料列，使用索引進行比對
    for i in range(max_length):
        if teacher_list[i] == teachername and end_time_list[i] == '':
            return i + 1  # 返回符合條件的行號，因為 get_col() 返回的索引是 0-based，所以這裡要加 1
    return 'Error'  # 如果找不到符合條件的行，返回 'Error'
        
# find start time
def get_startTime(row):
    return sheet_dataForthisMonth.get_value((row, 2))
# find duration
def get_duration(row):
    return sheet_dataForthisMonth.get_value((row, 6))
# find progress
def get_progress(row):
    return sheet_dataForthisMonth.get_value((row, 7))
# find homework
def get_homework(row):
    return sheet_dataForthisMonth.get_value((row, 8))

# progress更新
def update_progress(teacherId, classingRow, messageStr):
    update_cell_data(sheet_dataForthisMonth, classingRow, 7, messageStr)
    update_teacherState(teacherId, 'addingHomework')

# homework更新
def update_homework(teacherId, classingRow, messageStr):
    update_cell_data(sheet_dataForthisMonth, classingRow, 8, messageStr)
    update_teacherState(teacherId, 'normal')

# 上課打卡通知格式
def getFlexStartTimeMessageF(date_str, time_str, name):
    return FlexSendMessage(
        alt_text='課程已開始',
        contents={
  "type": "bubble",
  "size": "kilo",
  "body": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "contents": [
      {
        "type": "text",
        "text": f"{name}今日課程已開始",
        "weight": "bold",
        "size": "xl",
        "color": "#2768A8",
        "align": "center",
        "margin": "lg"
      },
      {
        "type": "box",
        "layout": "vertical",
        "spacing": "md",
        "margin": "xl",
        "contents": [
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": "上課日期",
                "weight": "bold",
                "color": "#2768A8",
                "margin": "sm"
              },
              {
                "type": "text",
                "text": date_str,
                "size": "sm",
                "color": "#AAAAAA",
                "align": "end"
              }
            ]
          },
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": "上課時間",
                "weight": "bold",
                "color": "#2768A8",
                "flex": 0,
                "margin": "sm"
              },
              {
                "type": "text",
                "text": time_str,
                "size": "sm",
                "color": "#AAAAAA",
                "align": "end"
              }
            ]
          }
        ]
      },
      {
        "type": "text",
        "text": f"請記得下課打卡！",
        "size": "sm",
        "color": "#AAAAAA",
        "align": "center",
        "margin": "lg"
      }
    ]
  },
  "styles": {
    "body": {
      "backgroundColor": "#FFFFFF"
    }
  }
})

# 本次上課時間確認格式
def getFlexTimeMessageF(time1, time2, name, duration):
    getFlexTimeMessage = FlexSendMessage(
        alt_text='本次上課時間',
        contents={
  "type": "bubble",
  "size": "kilo",
  "direction": "ltr",
  "body": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "action": {
      "type": "uri",
      "label": "Action",
      "uri": "https://superb-tutor.com"
    },
    "contents": [
      {
        "type": "text",
        "text": "本次上課資訊",
        "weight": "bold",
        "size": "xl",
        "color": "#2768A8",
        "align": "center",
        "margin": "lg"
      },
      {
        "type": "box",
        "layout": "vertical",
        "spacing": "md",
        "margin": "xl",
        "contents": [
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": "上課時間",
                "weight": "bold",
                "color": "#2768A8",
                "margin": "sm"
              },
              {
                "type": "text",
                "text": time1,
                "size": "sm",
                "color": "#AAAAAA",
                "align": "end"
              }
            ]
          },
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": "下課時間",
                "weight": "bold",
                "color": "#2768A8",
                "flex": 0,
                "margin": "sm"
              },
              {
                "type": "text",
                "text": time2,
                "size": "sm",
                "color": "#AAAAAA",
                "align": "end"
              }
            ]
          }
        ]
      },
      {
        "type": "text",
        "text": f"{name}本次上課時間共計 {duration}",
        "size": "sm",
        "color": "#AAAAAA",
        "align": "center",
        "margin": "lg",
        "decoration": "underline"
      }
    ]
  },
  "footer": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "button",
        "action": {
          "type": "message",
          "label": "確認登記",
          "text": "已確認本次上課資訊無誤，確認登記！"
        },
        "color": "#F3B237",
        "style": "primary"
      }
    ]
  },
  "styles": {
    "body": {
      "backgroundColor": "#FFFFFF"
    },
    "footer": {
      "backgroundColor": "#FFFFFF"
    }
  }
})
    return getFlexTimeMessage

# 本次上課時間確認格式2
def getFlexTimeMessageF2(time1, time2, name, duration, progress, homework):
    getFlexTimeMessage = FlexSendMessage(
        alt_text='本次上課資訊',
        contents={
  "type": "bubble",
  "size": "kilo",
  "direction": "ltr",
  "body": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "action": {
      "type": "uri",
      "label": "Action",
      "uri": "https://superb-tutor.com"
    },
    "contents": [
      {
        "type": "text",
        "text": "本次上課資訊",
        "weight": "bold",
        "size": "xl",
        "color": "#2768A8",
        "align": "center",
        "margin": "lg"
      },
      {
        "type": "box",
        "layout": "vertical",
        "spacing": "md",
        "margin": "xl",
        "contents": [
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": "上課時間",
                "weight": "bold",
                "color": "#2768A8",
                "margin": "sm"
              },
              {
                "type": "text",
                "text": time1,
                "size": "sm",
                "color": "#AAAAAA",
                "align": "end"
              }
            ]
          },
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": "下課時間",
                "weight": "bold",
                "color": "#2768A8",
                "flex": 0,
                "margin": "sm"
              },
              {
                "type": "text",
                "text": time2,
                "size": "sm",
                "color": "#AAAAAA",
                "align": "end"
              }
            ]
          }
        ]
      },
      {
        "type": "text",
        "text": f"{name}本次上課時間共計 {duration}",
        "size": "sm",
        "color": "#AAAAAA",
        "align": "center",
        "margin": "lg",
        "decoration": "underline"
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "上課進度",
                "weight": "bold",
                "color": "#2768A8",
                "margin": "sm",
                "contents": []
              },
              {
                "type": "text",
                "text": progress,
                "size": "sm",
                "color": "#AAAAAA",
                "align": "start",
                "margin": "xs",
                "contents": []
              }
            ]
          },
          {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "作業",
                "weight": "bold",
                "color": "#2768A8",
                "margin": "sm",
                "contents": []
              },
              {
                "type": "text",
                "text": homework,
                "size": "sm",
                "color": "#AAAAAA",
                "margin": "xs",
                "contents": []
              }
            ]
          }
        ]
      }
    ]
  },
  "footer": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "button",
        "action": {
          "type": "message",
          "label": "確認登記",
          "text": "已確認本次上課資訊無誤，確認登記！"
        },
        "color": "#F3B237",
        "style": "primary"
      }
    ]
  },
  "styles": {
    "body": {
      "backgroundColor": "#FFFFFF"
    },
    "footer": {
      "backgroundColor": "#FFFFFF"
    }
  }
})
    return getFlexTimeMessage


# 下次上課時間通知格式
def getFlexNextTimeMessageF(time1, time2):
    getFlexTimeMessage = FlexSendMessage(
        alt_text='下次上課時間通知',
        contents={
  "type": "bubble",
  "size": "kilo",
  "direction": "ltr",
  "body": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "action": {
      "type": "uri",
      "label": "Action",
      "uri": "https://superb-tutor.com"
    },
    "contents": [
      {
        "type": "text",
        "text": "下次上課時間",
        "weight": "bold",
        "size": "xl",
        "color": "#FFFFFF",
        "align": "center",
        "margin": "lg"
      },
      {
        "type": "box",
        "layout": "vertical",
        "spacing": "md",
        "margin": "xl",
        "contents": [
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": "上課日期",
                "weight": "bold",
                "color": "#FFFFFF",
                "margin": "sm"
              },
              {
                "type": "text",
                "text": time1,
                "size": "sm",
                "color": "#CACAC7FF",
                "align": "end"
              }
            ]
          },
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": "上課時間",
                "weight": "bold",
                "color": "#FFFFFF",
                "flex": 0,
                "margin": "sm"
              },
              {
                "type": "text",
                "text": time2,
                "size": "sm",
                "color": "#CACAC7FF",
                "align": "end"
              }
            ]
          }
        ]
      },
      {
        "type": "text",
        "text": "如有需更動請儘早通知",
        "size": "sm",
        "color": "#CACAC7FF",
        "align": "center",
        "margin": "lg"
      }
    ]
  },
  "footer": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "button",
        "action": {
          "type": "message",
          "label": "確認",
          "text": f"確認下次上課時間為\n{time1}  {time2}！"
        },
        "color": "#F3B237",
        "style": "primary"
      }
    ]
  },
  "styles": {
    "body": {
      "backgroundColor": "#2768A8"
    },
    "footer": {
      "backgroundColor": "#2768A8"
    }
  }
})
    return getFlexTimeMessage

######################################################

app = Flask(__name__)

# 從環境變數中讀取 LINE Bot 的 Channel Access Token 和 Channel Secret
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.type == 'message':
        if event.message.type == 'text':
            message_text = event.message.text
            # test
            if message_text == 'hi':
                replyTextMessage = TextSendMessage(text='Hello! I\'m Superb Tutor Bot!')
            # 快速選單
            elif message_text == '精湛' or message_text == '精湛教育' or message_text == '選單':
                flex_message = TextSendMessage(text="請選擇選單",quick_reply=QuickReply(items=[QuickReplyButton(action=MessageAction(label="老師選單", text="老師選單")),QuickReplyButton(action=MessageAction(label="家長選單", text="家長選單")),QuickReplyButton(action=MessageAction(label="行政選單", text="行政選單"))]))
                line_bot_api.reply_message(event.reply_token, flex_message)
            # 呼叫老師選單
            elif message_text == '老師選單':
                currentDateAndTime = datetime.now()
                newDateAndTime = currentDateAndTime + timedelta(hours=8)
                currentTimeTemplate = newDateAndTime.strftime('%Y-%m-%dT%H:%M')
                replyFlexMessage = TemplateSendMessage(
                    alt_text='老師功能選單',
                    template=ButtonsTemplate(
                        thumbnail_image_url="https://i.imgur.com/V4VOSTQ.png",
                        image_aspect_ratio="rectangle",
                        image_size="cover",
                        image_background_color="#2768A8",
                        title="老師功能選單",
                        text="請選擇要執行的功能：",
                        actions=[
                            MessageTemplateAction(
                                label='上下課打卡',
                                text='打卡功能'
                            ),
                            DatetimePickerTemplateAction(
                                label='通知下次上課時間',
                                data='下次上課時間',
                                mode='datetime',
                                initial=currentTimeTemplate,
                                max='2030-07-18T12:00',
                                min='2024-01-01T12:00'
                            ),
                            MessageTemplateAction(
                                label='登記本次進度作業',
                                text='登記本次進度作業'
                            )
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, replyFlexMessage)
            # 呼叫家長選單
            elif message_text == '家長選單':
                replyTextMessage = TextSendMessage(text='家長選單功能尚未開放！')
            # 呼叫行政選單（已加入老師限制）
            elif message_text == '行政選單' and get_teacherState(event.source.user_id) == 'normal':
                replyFlexMessage = TemplateSendMessage(
                    alt_text='行政功能選單',
                    template=ButtonsTemplate(
                        thumbnail_image_url="https://i.imgur.com/V4VOSTQ.png",
                        image_aspect_ratio="rectangle",
                        image_size="cover",
                        image_background_color="#2768A8",
                        title="行政功能選單",
                        text="請選擇要執行的功能：",
                        actions=[
                            MessageTemplateAction(
                                label='登錄老師名字',
                                text='登錄老師名字'
                            ),
                            MessageTemplateAction(
                                label='設定群組學生資訊',
                                text='設定群組學生資訊'
                            )
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, replyFlexMessage)
            # 打卡（已加入老師限制）
            elif message_text == '打卡功能' and get_teacherState(event.source.user_id) == 'normal':
                currentDateAndTime = datetime.now()
                newDateAndTime = currentDateAndTime + timedelta(hours=8)
                currentTimeTemplate = newDateAndTime.strftime('%Y-%m-%dT%H:%M')
                replyFlexMessage = TemplateSendMessage(
                    alt_text='選時間確認',
                    template=ConfirmTemplate(
                        text='老師打卡',
                        actions=[
                            DatetimePickerTemplateAction(
                                label='上課',
                                data='資料上課',
                                mode='datetime',
                                initial=currentTimeTemplate,
                                max='2030-07-18T12:00',
                                min='2024-01-01T12:00'
                            ),
                            DatetimePickerTemplateAction(
                                label='下課',
                                data='資料下課',
                                mode='datetime',
                                initial=currentTimeTemplate,
                                max='2030-07-18T12:00',
                                min='2024-01-01T12:00'
                            )
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, replyFlexMessage)
            # 登記本次進度作業（加入老師限制）
            elif message_text == '登記本次進度作業' and get_teacherState(event.source.user_id) == 'normal':
                update_teacherState(event.source.user_id, 'addingProgress')
                replyTextMessage = TextSendMessage(text='請輸入課程的進度：')
            # 登記老師
            elif message_text == '登錄老師名字':
                add_teacherInfo(event.source.user_id)
                replyTextMessage = TextSendMessage(text='請輸入您的名字：')
            # 紀錄老師名字
            elif get_teacherState(event.source.user_id) == 'adding':
                update_teacherInfo(event.source.user_id, message_text)
                replyTextMessage = TextSendMessage(text='您已成功將此帳號登記為 '+message_text+' 老師！\n(請勿重複登記)')
            # 設定群組學生資訊
            elif message_text == '設定群組學生資訊':
                add_groupInfo(event.source.group_id, event.source.user_id)
                replyTextMessage = TextSendMessage(text='請輸入學生名字：')
            # 登記本次進度作業
            elif get_teacherState(event.source.user_id) == 'addingProgress':
                row = find_classingRow(event.source.user_id)
                if row != 'Error':
                    update_progress(event.source.user_id, row, message_text)
                    replyTextMessage = TextSendMessage(text='請輸入本次作業的內容：')
                else:
                    update_teacherState(event.source.user_id, 'normal')
                    replyTextMessage = TextSendMessage(text="無法找到對應的上課時間資料。")
                    line_bot_api.reply_message(event.reply_token, replyTextMessage)
            # 紀錄本次進度作業
            elif get_teacherState(event.source.user_id) == 'addingHomework':
                row = find_classingRow(event.source.user_id)
                if row != 'Error':
                    update_homework(event.source.user_id, row, message_text)
                    replyTextMessage = TextSendMessage(text='成功登記本次進度作業！\n\n請記得於群組進行下課打卡，以發送課程通知！')                
                else:
                    update_teacherState(event.source.user_id, 'normal')
                    replyTextMessage = TextSendMessage(text="無法找到對應的上課時間資料。")
                    line_bot_api.reply_message(event.reply_token, replyTextMessage)
            # 紀錄學生名字
            elif get_groupState(event.source.group_id) == 'addingStudent':
                update_groupInfoStudent(event.source.group_id, message_text)
                replyTextMessage = TextSendMessage(text='請輸入老師名字：')
            # 紀錄老師名字
            elif get_groupState(event.source.group_id) == 'addingTeacher':
                update_groupInfoTeacher(event.source.group_id, message_text)
                replyTextMessage = TextSendMessage(text='您已成功設定此群組學生資訊！\n(請勿重複設定)')

            line_bot_api.reply_message(event.reply_token, replyTextMessage)

# 處理 postback 事件
@handler.add(PostbackEvent)
def handle_postback(events):
    if events.type == 'postback':
        datetime_str = events.postback.params['datetime']
        # 解析 datetime
        message_dateTime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        # 轉為字串
        message_dateTime_str = message_dateTime.strftime('日期: %Y-%m-%d, 時間: %H:%M')
        if events.postback.data == '資料上課':
            add_startTime(events.source.user_id, events.source.group_id, message_dateTime)
            dateStr = message_dateTime.strftime('%Y / %m / %d')
            timeStr = message_dateTime.strftime('%H:%M')
            namestr = get_groupName(events.source.group_id)
            flexMessage = getFlexStartTimeMessageF(dateStr, timeStr, namestr)
            line_bot_api.reply_message(events.reply_token, flexMessage)
        elif events.postback.data == '資料下課':
            row = find_endTimeRow(events.source.user_id, message_dateTime)
            if row != 'Error':
                add_endTime(row, message_dateTime)
                startTimeStr = get_startTime(row)
                endTimeStr = message_dateTime.strftime('%H:%M')
                duration = get_duration(row)
                namestr = get_groupName(events.source.group_id)
                progress = get_progress(row)
                homework = get_homework(row)
                if progress == '' and homework == '':
                  flexMessage = getFlexTimeMessageF(startTimeStr, endTimeStr, namestr, duration)
                else:
                  flexMessage = getFlexTimeMessageF2(startTimeStr, endTimeStr, namestr, duration, progress, homework)
                line_bot_api.reply_message(events.reply_token, flexMessage)
            else:
                replyTextMessage = TextSendMessage(text="無法找到對應的上課時間資料。")
                line_bot_api.reply_message(events.reply_token, replyTextMessage)
        elif events.postback.data == '下次上課時間':
            DateStr = message_dateTime.strftime('%m / %d')
            TimeStr = message_dateTime.strftime('%H:%M')
            flexMessage = getFlexNextTimeMessageF(DateStr, TimeStr)
            line_bot_api.reply_message(events.reply_token, flexMessage)
                
        # 構建回覆訊息
        replyTextMessage = TextSendMessage(text=message_dateTime_str)
        line_bot_api.reply_message(events.reply_token, replyTextMessage)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)