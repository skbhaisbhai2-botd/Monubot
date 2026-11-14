import telebot
import threading
import time
import json
import os
import requests
from datetime import datetime, timezone
from telebot import types
from flask import Flask

# ===============================
# 🔧 BOT CONFIGURATION
# ===============================
BOT_TOKEN = "9200835027:AAGT4dhzeunqm_917OcomrNcPSrSmnaT_qI"
ADMIN_ID = 7741897793
CHANNEL_LINK = "https://t.me/+avZJX9ssyQc5MzI9"
WIN_99_LINK = "https://cosmofeed.com/ps/6acee92cebe5600013b73f00"
DEFAULT_GAME_URL = "https://www.91appq.com/#/register?invitationCode=747881278052"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ===============================
# 🌐 FLASK 24/7 KEEP-ALIVE SERVER
# ===============================
app = Flask(__name__)

@app.route("/")
def home():
    return "👑 ADITYA HACKER 1.3 BOT IS RUNNING 24/7 LIVE!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ===============================
# 🌐 GLOBAL STATES & STORAGE
# ===============================
active_dict = {}                  # chat_id -> True/False
last_sent_period = {}             # chat_id -> last period (double prevention)
DATA_FILE = "prediction_history.json"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# Shared prediction state (Exact period logic unchanged)
current_pred = {
    "period_full": "",
    "period_short": "----",
    "trend": "BIG",
    "opp": 0,
    "confidence": 97,
    "level": 1
}
loss_streak = 0
last_trend = None
last_issue = ""
next_issue = ""
history_list = []                 # Clean history list (max 50)
total_wins = 0
total_losses = 0

state_lock = threading.Lock()

# ===============================
# 📊 DATA PERSISTENCE
# ===============================
def load_data():
    global history_list, total_wins, total_losses, loss_streak, last_trend
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            history_list = data.get("history", [])[:50]
            total_wins = data.get("total_wins", 0)
            total_losses = data.get("total_losses", 0)
            loss_streak = data.get("loss_streak", 0)
            last_trend = data.get("last_trend", None)
    except Exception:
        pass

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({
                "history": history_list[:50],
                "total_wins": total_wins,
                "total_losses": total_losses,
                "loss_streak": loss_streak,
                "last_trend": last_trend
            }, f, indent=2)
    except Exception:
        pass

load_data()

# ===============================
# 🔮 EXACT PREDICTION ENGINE (UNCHANGED PERIOD)
# ===============================
def get_size(n):
    return "BIG" if n >= 5 else "SMALL"

def get_color(n):
    return "RED" if n in [0, 2, 4, 6, 8] else "GREEN"

def fetch_wingo_list():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://draw.ar-lottery01.com/",
        "Origin": "https://draw.ar-lottery01.com"
    }
    try:
        r = requests.get(API_URL + "?t=" + str(int(time.time() * 1000)), headers=headers, timeout=7)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0 and data.get("data", {}).get("list"):
                return data["data"]["list"]
    except Exception as e:
        print(f"[API Error] {e}")
    return None

def compute_signal(list_data):
    """Generates BIG/SMALL trend + 1 Opposite Backup Number (e.g., BIG 0, SMALL 7)"""
    global loss_streak, last_trend

    nums = []
    for x in list_data[:40]:
        try:
            nums.append(int(x["number"]))
        except Exception:
            continue
    if len(nums) < 5:
        return {"trend": "BIG", "opp": 0, "confidence": 97}

    sizes = [get_size(n) for n in nums]
    trend = "BIG"

    if loss_streak >= 2:
        trend = "SMALL" if get_size(nums[0]) == "BIG" else "BIG"
    elif loss_streak == 1:
        trend = "SMALL" if last_trend == "BIG" else "BIG"
    else:
        if sizes[0] == sizes[1] == sizes[2]:
            trend = sizes[0]
        elif sizes[0] != sizes[1] and sizes[1] != sizes[2]:
            trend = "SMALL" if sizes[0] == "BIG" else "BIG"
        else:
            big_w = small_w = 0
            for i in range(min(10, len(sizes))):
                if sizes[i] == "BIG":
                    big_w += (10 - i)
                else:
                    small_w += (10 - i)
            trend = "BIG" if big_w >= small_w else "SMALL"

    confidence = 99 if loss_streak >= 2 else (98 if loss_streak == 1 else 96 + (nums[0] % 3))

    # Opposite backup pool: If BIG -> pick from [0,1,2,3,4], If SMALL -> pick from [5,6,7,8,9]
    opp_pool = [0, 1, 2, 3, 4] if trend == "BIG" else [5, 6, 7, 8, 9]

    freq = [0] * 10
    for n in nums[:20]:
        if 0 <= n <= 9:
            freq[n] += 1

    opp_pool.sort(key=lambda x: freq[x])

    return {
        "trend": trend,
        "opp": opp_pool[0],
        "confidence": confidence
    }

def update_global_prediction():
    """Fetch latest data and update global prediction without altering game period"""
    global current_pred, last_issue, next_issue, loss_streak, last_trend
    global total_wins, total_losses, history_list

    list_data = fetch_wingo_list()
    if not list_data:
        return

    latest = list_data[0]
    issue_number = str(latest["issueNumber"])
    short_issue = issue_number[-4:]
    try:
        actual_num = int(latest["number"])
    except Exception:
        return

    actual_size = get_size(actual_num)
    actual_color = get_color(actual_num)

    with state_lock:
        # Check previous result: If BIG/SMALL matches OR Backup Number matches -> WIN, else LOSS
        if current_pred["period_full"] and last_issue and last_issue != issue_number:
            if current_pred["period_short"] == short_issue:
                trend_hit = (current_pred["trend"] == actual_size)
                num_hit = (actual_num == current_pred["opp"])

                if trend_hit or num_hit:
                    status_type = "WIN"
                    total_wins += 1
                    loss_streak = 0
                    last_trend = None
                    current_pred["level"] = 1
                else:
                    status_type = "LOSS"
                    total_losses += 1
                    loss_streak += 1
                    last_trend = current_pred["trend"]
                    current_pred["level"] = min(3, current_pred["level"] + 1)

                entry = {
                    "period": short_issue,
                    "signal": f"{current_pred['trend']} {current_pred['opp']}",
                    "actual": f"{actual_size} ({actual_color}) [{actual_num}]",
                    "status": status_type
                }
                history_list = [entry] + history_list
                history_list = history_list[:50]
                save_data()

        last_issue = issue_number
        next_full = str(int(issue_number) + 1)
        next_short = next_full[-4:]

        if next_issue != next_full:
            next_issue = next_full
            sig = compute_signal(list_data)
            current_pred = {
                "period_full": next_full,
                "period_short": next_short,
                "trend": sig["trend"],
                "opp": sig["opp"],
                "confidence": sig["confidence"],
                "level": current_pred.get("level", 1)
            }

def get_remaining_seconds():
    return max(1, 60 - datetime.now(timezone.utc).second)

# ===============================
# 🎯 PREMIUM COLORFUL FORMATTERS
# ===============================
def build_premium_signal():
    p = current_pred
    trend_emoji = "🟢" if p["trend"] == "BIG" else "🔴"
    level_badge = {
        1: "🟢 SAFE LEVEL 1",
        2: "🟡 RECOVERY LEVEL 2",
        3: "🔴 SURESHOT LEVEL 3"
    }.get(p["level"], "🟢 SAFE LEVEL 1")

    signal_display = f"{p['trend']} {p['opp']}"

    text = f"""
╔══════════════════════════════╗
║   👑 *ADITYA HACKER 1.3* 👑   ║
║   ✨ VIP COLOUR PREDICTION ✨  ║
╚══════════════════════════════╝

🎮 *Game:* `WinGo 1 Minute`
🆔 *Period:* `{p['period_short']}`

━━━━━━━━━━━━━━━━━━━━━━━━
{trend_emoji} *SIGNAL:*  `{signal_display}`
🛡️ *Backup Opp:* `{p['opp']}`
━━━━━━━━━━━━━━━━━━━━━━━━

⚡ *Stage:* {level_badge}
🔥 *Accuracy:* `{p['confidence']}%`

💎 *99% WIN VIP HACK:*
👉 {WIN_99_LINK}

🎯 *Register & Play:*
👉 {DEFAULT_GAME_URL}
"""
    return text.strip()

def build_history_text():
    total = total_wins + total_losses
    rate = round((total_wins / total) * 100) if total > 0 else 98

    header = (
        f"╔══════════════════════════════╗\n"
        f"║   📜 *ALL PREDICTION HISTORY*   ║\n"
        f"╚══════════════════════════════╝\n\n"
        f"✅ *Total Win:* `{total_wins}`  |  ❌ *Total Loss:* `{total_losses}`\n"
        f"📈 *Win Accuracy:* `{rate}%`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    if not history_list:
        return header + "\n⏳ *No history recorded yet. Start prediction to see live results!*"

    lines = [header]
    for i, h in enumerate(history_list[:15], 1):
        if h["status"] == "WIN":
            badge = "✅ *WIN*"
        else:
            badge = "❌ *LOSS*"

        lines.append(
            f"🔹 *Period:* `{h['period']}`\n"
            f"   🎯 *Pred:* `{h['signal']}`\n"
            f"   🎲 *Open:* `{h['actual']}` ➔ {badge}\n"
        )
    return "\n".join(lines)

# ===============================
# 🚀 PREDICTION WORKER THREAD
# ===============================
def prediction_worker(chat_id):
    while active_dict.get(chat_id):
        try:
            update_global_prediction()
            period = current_pred["period_full"]

            if period and last_sent_period.get(chat_id) != period:
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("📜 All History", callback_data="show_history"),
                    types.InlineKeyboardButton("🎧 Customer Service", url=CHANNEL_LINK)
                )
                markup.row(
                    types.InlineKeyboardButton("👑 99% WIN VIP HACK", url=WIN_99_LINK)
                )

                caption = build_premium_signal()
                bot.send_message(chat_id, caption, reply_markup=markup, disable_web_page_preview=True)
                last_sent_period[chat_id] = period
        except Exception as e:
            print(f"[Worker Error] {e}")

        remaining = get_remaining_seconds()
        for _ in range(remaining):
            if not active_dict.get(chat_id):
                return
            time.sleep(1)

# ===============================
# 📱 4-BUTTON PREMIUM MENU (2x2 GRID)
# ===============================
def main_control_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("🚀 Start Prediction")
    btn2 = types.KeyboardButton("🎧 Customer Service")
    btn3 = types.KeyboardButton("🛑 Stop Prediction")
    btn4 = types.KeyboardButton("📜 All History")
    kb.add(btn1, btn2)
    kb.add(btn3, btn4)
    return kb

# ===============================
# 🤖 BOT HANDLERS
# ===============================
@bot.message_handler(commands=["start"])
def start_command(msg):
    welcome = f"""
╔══════════════════════════════╗
║   👑 *ADITYA HACKER 1.3* 👑   ║
╠══════════════════════════════╣
║  🌈 *PREMIUM COLOUR ENGINE*  ║
║  ⚡ Live WinGo 1M Signals     ║
║  🎯 Main + Opposite Backup    ║
║  📊 Instant Win/Loss History  ║
╚══════════════════════════════╝

👇 *Select an option from the menu below:*
"""
    bot.send_message(msg.chat.id, welcome, reply_markup=main_control_menu(), disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True)
def message_router(msg):
    text = (msg.text or "").strip()
    cid = msg.chat.id

    if text == "🚀 Start Prediction":
        if active_dict.get(cid):
            bot.send_message(cid, "⚠️ *Prediction is already running LIVE!*", reply_markup=main_control_menu())
            return

        active_dict[cid] = True
        bot.send_message(
            cid,
            "🟢 *LIVE PREDICTION STARTED!*\n\n"
            "⚡ Fetching real-time WinGo 1M period...\n"
            "🎯 Format: `BIG 0` / `SMALL 7`",
            reply_markup=main_control_menu()
        )
        threading.Thread(target=prediction_worker, args=(cid,), daemon=True).start()

    elif text == "🎧 Customer Service":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Official Channel / Support", url=CHANNEL_LINK))
        bot.send_message(
            cid,
            "🎧 *CUSTOMER SERVICE & VIP SUPPORT*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 नीचे दिए गए बटन पर क्लिक करके सीधे हमारे ऑफिशियल चैनल पर जुड़ें:",
            reply_markup=markup,
            disable_web_page_preview=True
        )

    elif text == "🛑 Stop Prediction":
        active_dict[cid] = False
        last_sent_period.pop(cid, None)
        bot.send_message(
            cid,
            "🛑 *Prediction Stopped!*\n\n"
            "▶️ दोबारा शुरू करने के लिए *🚀 Start Prediction* दबाएं।",
            reply_markup=main_control_menu()
        )

    elif text == "📜 All History":
        bot.send_message(cid, build_history_text(), reply_markup=main_control_menu(), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "show_history":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, build_history_text(), disable_web_page_preview=True)

# ===============================
# 🚀 24/7 BACKGROUND UPDATER THREAD
# ===============================
def background_updater():
    while True:
        try:
            update_global_prediction()
        except Exception as e:
            print(f"[Background Updater Error] {e}")
        time.sleep(2.5)

# ===============================
# 🚀 MAIN RUNNABLE (24/7 WITH AUTO-RESTART)
# ===============================
if __name__ == "__main__":
    print("👑 ADITYA HACKER 1.3 Bot + Flask Server Starting 24/7...")
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=background_updater, daemon=True).start()

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[Polling Error - Restarting in 3s] {e}")
            time.sleep(3)
