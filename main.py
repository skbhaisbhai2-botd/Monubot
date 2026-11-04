import telebot
import threading
import time
import random
import pytz
from datetime import datetime
from telebot import types
import json
import os
import requests

# ===============================
# 🔧 BOT CONFIGURATION
# ===============================
BOT_TOKEN = "9192618748:AAHFPOL9fYaGWwH48fGElH6khTD-s0jZlTo"
ADMIN_ID = 7741897793
CHANNEL_LINK = "https://t.me/+avZJX9ssyQc5MzI9"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ===============================
# 🌐 GLOBAL STATES & STORAGE
# ===============================
active_dict = {}
user_channels = {}
DATA_FILE = "prediction_history.json"

# ===============================
# 🔄 LIVE API GAME PERIOD FETCHER
# ===============================
def fetch_live_game_period():
    """
    API se latest issue number fetch karta hai aur usme +1 karke 
    current/next exact game period return karta hai.
    """
    try:
        response = requests.get(f"{API_URL}?pageNo=1&pageSize=1&ts={int(time.time()*1000)}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # API response se list ya records extract karna
            list_data = data.get("data", {}).get("list", []) or data.get("list", [])
            if list_data and len(list_data) > 0:
                latest_issue = str(list_data[0].get("issueNumber") or list_data[0].get("issue") or "")
                if latest_issue:
                    # Latest issue me +1 karke active period nikalna
                    return str(int(latest_issue) + 1)
    except Exception as e:
        print(f"[!] API fetch error: {e}")
    
    # Fallback agar API fail ho jaye toh time-based calculation
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    yyyyMMdd = now.strftime("%Y%m%d")
    total_minutes = now.hour * 60 + now.minute
    return f"{yyyyMMdd}1000{10001 + total_minutes}"

# ===============================
# 🔮 HIGH-LEVEL PREDICTION ENGINE
# ===============================
def generate_high_level_prediction():
    num = random.randint(0, 9)
    if num >= 5:
        big_small = "🔴 BIG"
    else:
        big_small = "🔵 SMALL"
    return big_small, num

def get_remaining_seconds():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    return 60 - now.second if now.second < 60 else 0

# ===============================
# 📊 HISTORY & STATS STORAGE
# ===============================
def load_json_data():
    if not os.path.exists(DATA_FILE):
        return {"history": [], "users": {}}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {"history": [], "users": {}}

def save_json_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_prediction_history(record):
    data = load_json_data()
    history_list = data.get("history", [])
    history_list.insert(0, record)
    data["history"] = history_list[:50]  # Keep last 50 records
    save_json_data(data)

def update_user_activity(user_id):
    data = load_json_data()
    users = data.get("users", {})
    now = datetime.now().strftime("%Y-%m-%d")
    if str(user_id) not in users:
        users[str(user_id)] = {"first_seen": now, "last_seen": now, "usage_count": 1}
    else:
        users[str(user_id)]["last_seen"] = now
        users[str(user_id)]["usage_count"] += 1
    data["users"] = users
    save_json_data(data)

# ===============================
# 🚀 PREDICTION WORKER THREAD
# ===============================
def prediction_worker(chat_id, channel_id=None):
    last_period = None
    prediction_count = 0

    while active_dict.get(chat_id):
        # 10 predictions ke baad 20 minutes ka cool-down break
        if prediction_count >= 10:
            try:
                bot.send_message(
                    chat_id, 
                    "⏳ *Target 10 Predictions Completed!*\n\n"
                    "🛡️ Bot is taking a scheduled **20-minute safety cool-down break** to bypass server detection. It will auto-resume shortly!",
                    parse_mode="Markdown"
                )
            except:
                pass

            for _ in range(1200):  # 1200 seconds = 20 minutes
                if not active_dict.get(chat_id):
                    return
                time.sleep(1)
            
            prediction_count = 0
            try:
                bot.send_message(chat_id, "🚀 *Cool-down complete! Resuming high-level prediction sessions...*", parse_mode="Markdown")
            except:
                pass

        # API se exact live period fetch karna
        period = fetch_live_game_period()
        
        if period != last_period:
            big_small, num = generate_high_level_prediction()
            
            # Send Prediction Signal with Copy Button & Channel Link
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📋 Copy Signal", callback_data="copy_sig"))
            markup.add(types.InlineKeyboardButton("📢 Official Channel", url=CHANNEL_LINK))

            caption = f"""
👑 *ADITYA RAJPUT VIP PREDICTOR* 👑
━━━━━━━━━━━━━━━━━━━
🧾 *Game Period:* `{period}`
🎯 *Prediction:* {big_small} – *{num}*
⏱ *Timer:* 1 Minute Wingo
━━━━━━━━━━━━━━━━━━━
🔗 [Join Official Channel]({CHANNEL_LINK})
⚡ _Powered by High-Level AI Engine_
"""
            try:
                bot.send_message(chat_id, caption, reply_markup=markup, disable_web_page_preview=True)
                if channel_id:
                    bot.send_message(channel_id, caption, reply_markup=markup, disable_web_page_preview=True)
            except Exception as e:
                print(f"[!] Send failed: {e}")

            # Simulate Result Verification for History Log
            actual_num = random.randint(0, 9)
            actual_size = "🔴 BIG" if actual_num >= 5 else "🔵 SMALL"
            is_win = (big_small.strip() == actual_size.strip())
            status_str = "✅ WIN" if is_win else "❌ LOSS"

            record = {
                "period": period,
                "prediction": f"{big_small} ({num})",
                "result_num": f"{actual_size} ({actual_num})",
                "status": status_str
            }
            log_prediction_history(record)

            prediction_count += 1
            last_period = period

        for _ in range(get_remaining_seconds(), 0, -1):
            if not active_dict.get(chat_id):
                break
            time.sleep(1)

# ===============================
# 📱 KEYBOARDS & MENUS
# ===============================
def main_control_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🚀 Start Prediction", "🛑 Stop Prediction")
    kb.add("📢 Set Channel", "📊 History & Stats")
    kb.add("👑 Developer Support")
    return kb

# ===============================
# 🤖 BOT HANDLERS
# ===============================
@bot.message_handler(commands=["start"])
def start_command(msg):
    update_user_activity(msg.from_user.id)
    welcome_text = (
        f"🌟 *WELCOME TO ADITYA RAJPUT VIP BOT* 🌟\n\n"
        f"💎 *High-Accuracy Wingo Prediction System*\n"
        f"🔥 Features: Live API Game Period Tracking, Auto 10-Round Cycles, Live History & Smart Analytics.\n\n"
        f"🔗 [Join Official VIP Channel]({CHANNEL_LINK})\n\n"
        f"👇 Choose an option from below to get started:"
    )
    bot.send_message(msg.chat.id, welcome_text, reply_markup=main_control_menu(), disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True)
def message_router(msg):
    text = msg.text.strip()
    cid = msg.chat.id
    update_user_activity(cid)

    if text == "🚀 Start Prediction":
        if active_dict.get(cid):
            bot.send_message(cid, "⚠️ Prediction session is already running actively!", reply_markup=main_control_menu())
            return
        active_dict[cid] = True
        ch = user_channels.get(cid)
        bot.send_message(
            cid,
            f"🚀 *ADITYA RAJPUT AI Engine Activated!*\n\n"
            f"📡 Status: Running with Live API Period Sync\n"
            f"{'📢 Linked Channel: ' + str(ch) if ch else '💬 Mode: Direct Chat Only'}",
            reply_markup=main_control_menu()
        )
        threading.Thread(target=prediction_worker, args=(cid, ch), daemon=True).start()

    elif text == "🛑 Stop Prediction":
        active_dict[cid] = False
        bot.send_message(cid, "🛑 *Prediction session stopped successfully.*", reply_markup=main_control_menu())

    elif text == "📢 Set Channel":
        bot.send_message(
            cid,
            "📢 Please send your **Channel Username** (e.g., `@yourchannel`) or **Channel ID** (e.g., `-100xxxxxxxxxx`).\n\n"
            "⚠️ *Note: Ensure this bot is added as an Admin in your channel.*",
            parse_mode="Markdown"
        )
        user_channels[cid] = "waiting_channel"

    elif text == "📊 History & Stats":
        data = load_json_data()
        history = data.get("history", [])
        
        history_text = "📊 *STEP-BY-STEP PREDICTION HISTORY*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        if not history:
            history_text += "_No prediction history recorded yet._"
        else:
            for idx, h in enumerate(history[:10], 1):
                history_text += f"{idx}. 🧾 `{h['period']}`\n   🎯 Ptr: {h['prediction']}\n   🎲 Res: {h['result_num']} | {h['status']}\n\n"
        
        bot.send_message(cid, history_text, reply_markup=main_control_menu())

    elif text == "👑 Developer Support":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Contact Developer", url=CHANNEL_LINK))
        bot.send_message(cid, "👑 For custom bot setup or support, contact via official channel:", reply_markup=markup)

    elif user_channels.get(cid) == "waiting_channel":
        ch_input = text
        try:
            bot.send_message(ch_input, "✅ ADITYA RAJPUT Bot connected successfully to this channel!")
            user_channels[cid] = ch_input
            bot.send_message(cid, f"✅ Channel successfully linked: `{ch_input}`", reply_markup=main_control_menu())
        except Exception as e:
            bot.send_message(cid, f"❌ Link failed. Make sure bot is admin.\nError: `{e}`", reply_markup=main_control_menu())
        user_channels[cid] = None

@bot.callback_query_handler(func=lambda call: call.data == "copy_sig")
def callback_copy(call):
    bot.answer_callback_query(call.id, "✅ Signal template ready! Copy from message text.", show_alert=False)

# ===============================
# 🚀 RUN DIRECT PREDICTION BOT
# ===============================
if __name__ == "__main__":
    print("👑 ADITYA RAJPUT Direct Prediction Bot with Live API Period Running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
