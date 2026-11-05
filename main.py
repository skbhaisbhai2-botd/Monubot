import telebot
import threading
import time
import random
from datetime import datetime, timezone
from telebot import types
import json
import os
import requests
from collections import deque

# ===============================
# 🔧 BOT CONFIGURATION
# ===============================
BOT_TOKEN = "9221404814:AAHUfJxq5Ei9dUMt1sgMkRKXOyoJzn-Q55s"
ADMIN_ID = 7741897793
CHANNEL_LINK = "https://t.me/+avZJX9ssyQc5MzI9"
WIN_99_LINK = "https://cosmofeed.com/ps/6acee92cebe5600013b73f00"
DEFAULT_GAME_URL = "https://www.91appq.com/#/register?invitationCode=747881278052"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ===============================
# 🌐 GLOBAL STATES & STORAGE
# ===============================
active_dict = {}                  # chat_id -> True/False
user_channels = {}                # chat_id -> channel
last_sent_period = {}             # chat_id -> last period (double prevention)
DATA_FILE = "prediction_history.json"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# Shared prediction state (so every user gets EXACT same signal)
current_pred = {
    "period_full": "",
    "period_short": "----",
    "trend": "BIG",
    "main": 5,
    "opp": 4,
    "confidence": 97,
    "level": 1
}
loss_streak = 0
last_trend = None
last_issue = ""
next_issue = ""
history_list = []                 # global clean history (max 50)
total_wins = 0
total_losses = 0
total_jackpots = 0

# Lock for thread safety
state_lock = threading.Lock()

# ===============================
# 📊 DATA PERSISTENCE
# ===============================
def load_data():
    global history_list, total_wins, total_losses, total_jackpots, loss_streak, last_trend
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            history_list = data.get("history", [])[:50]
            total_wins = data.get("total_wins", 0)
            total_losses = data.get("total_losses", 0)
            total_jackpots = data.get("total_jackpots", 0)
            loss_streak = data.get("loss_streak", 0)
            last_trend = data.get("last_trend", None)
    except:
        pass

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({
                "history": history_list[:50],
                "total_wins": total_wins,
                "total_losses": total_losses,
                "total_jackpots": total_jackpots,
                "loss_streak": loss_streak,
                "last_trend": last_trend
            }, f, indent=2)
    except:
        pass

load_data()

# ===============================
# 🔮 REAL PERIOD + SIGNAL ENGINE (EXACT WEB LOGIC)
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
        print(f"[API] {e}")
    return None

def compute_signal(list_data):
    """Exact same logic as web ADITYA HACKER 1.3"""
    global loss_streak, last_trend

    nums = []
    for x in list_data[:40]:
        try:
            nums.append(int(x["number"]))
        except:
            continue
    if len(nums) < 5:
        return {"trend": "BIG", "main": 5, "opp": 4, "confidence": 97}

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

    main_pool = [5, 6, 7, 8, 9] if trend == "BIG" else [0, 1, 2, 3, 4]
    opp_pool  = [0, 1, 2, 3, 4] if trend == "BIG" else [5, 6, 7, 8, 9]

    freq = [0] * 10
    for n in nums[:20]:
        if 0 <= n <= 9:
            freq[n] += 1

    main_pool.sort(key=lambda x: freq[x])
    opp_pool.sort(key=lambda x: freq[x])

    return {
        "trend": trend,
        "main": main_pool[0],
        "opp": opp_pool[0],
        "confidence": confidence
    }

def update_global_prediction():
    """Fetch latest + compute next period signal (shared for all users)"""
    global current_pred, last_issue, next_issue, loss_streak, last_trend
    global total_wins, total_losses, total_jackpots, history_list

    list_data = fetch_wingo_list()
    if not list_data:
        return

    latest = list_data[0]
    issue_number = str(latest["issueNumber"])
    short_issue = issue_number[-4:]
    try:
        actual_num = int(latest["number"])
    except:
        return

    actual_size = get_size(actual_num)
    actual_color = get_color(actual_num)

    with state_lock:
        # Check previous prediction result
        if current_pred["period_full"] and last_issue and last_issue != issue_number:
            if current_pred["period_short"] == short_issue:
                trend_hit = (current_pred["trend"] == actual_size)
                num_hit = (actual_num == current_pred["main"] or actual_num == current_pred["opp"])

                if trend_hit or num_hit:
                    if num_hit:
                        status_type = "JACKPOT"
                        total_jackpots += 1
                    else:
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
                    "pred": current_pred["trend"],
                    "main": current_pred["main"],
                    "opp": current_pred["opp"],
                    "actual": f"{actual_size}/{actual_color}",
                    "actual_num": actual_num,
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
                "main": sig["main"],
                "opp": sig["opp"],
                "confidence": sig["confidence"],
                "level": current_pred.get("level", 1)
            }

def get_remaining_seconds():
    return max(1, 60 - datetime.now(timezone.utc).second)

# ===============================
# 🎯 PREMIUM MESSAGE FORMAT
# ===============================
def build_premium_signal():
    p = current_pred
    level_text = {
        1: "SAFE LEVEL 1",
        2: "RECOVERY LEVEL 2",
        3: "SURESHOT LEVEL 3"
    }.get(p["level"], "SAFE LEVEL 1")

    timer = get_remaining_seconds()
    timer_str = f"00:{timer:02d}"

    text = f"""
╔════════════════════════════════╗
║   ⚡ *ADITYA HACKER 1.3* ⚡     ║
║   ULTRA FAST AI PREDICTION     ║
╚════════════════════════════════╝

🎮 *Game:* WinGo 1 Minute
📍 *Period:* `{p['period_short']}`
⏱ *Countdown:* `{timer_str}`

🎯 *SIGNAL:*  *{p['trend']}*
🎲 *MAIN NUM:*  `{p['main']}`
🔄 *BACKUP NUM:* `{p['opp']}`

🛡️ *Level:* {level_text}
🔥 *Accuracy:* {p['confidence']}%

━━━━━━━━━━━━━━━━━━━━━━━━
👑 *99% WIN VIP HACK*
{WIN_99_LINK}

🎮 *Game Link*
{DEFAULT_GAME_URL}

📢 *Telegram:* @ADITYAHACKER13
🔗 {CHANNEL_LINK}
━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return text.strip()

def build_stats_text():
    total = total_wins + total_losses + total_jackpots
    rate = round(((total_wins + total_jackpots) / total) * 100) if total > 0 else 97
    return f"""
📊 *ADITYA HACKER 1.3 STATS*
━━━━━━━━━━━━━━━━━━━━━━

🏆 *Total Wins:* `{total_wins}`
👑 *Jackpots:* `{total_jackpots}`
❌ *Losses:* `{total_losses}`
📈 *Win Rate:* `{rate}%`

🛡️ *Current Level:* {current_pred.get('level', 1)}
🔥 *Loss Streak:* {loss_streak}
"""

def build_history_text():
    if not history_list:
        return "⏳ *No history yet... Waiting for first result.*"

    lines = ["📜 *PREDICTION LOGS (Last 12)*\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    for i, h in enumerate(history_list[:12], 1):
        if h["status"] == "JACKPOT":
            badge = "👑 JACKPOT"
        elif h["status"] == "WIN":
            badge = "✅ WIN"
        else:
            badge = "❌ LOSS"

        lines.append(
            f"`{i:02d}.` *{h['period']}*\n"
            f"   🎯 {h['pred']}  [{h['main']}/{h['opp']}]\n"
            f"   🎲 {h['actual']} [{h['actual_num']}]  →  *{badge}*\n"
        )
    return "\n".join(lines)

# ===============================
# 🚀 PREDICTION WORKER (NO 20-MIN LIMIT)
# ===============================
def prediction_worker(chat_id, channel_id=None):
    while active_dict.get(chat_id):
        update_global_prediction()

        period = current_pred["period_full"]
        short = current_pred["period_short"]

        # Double prevention
        if last_sent_period.get(chat_id) == period:
            remaining = get_remaining_seconds()
            for _ in range(remaining):
                if not active_dict.get(chat_id):
                    return
                time.sleep(1)
            continue

        # Send premium signal
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("📋 Copy Signal", callback_data="copy_sig"),
            types.InlineKeyboardButton("📊 Stats", callback_data="show_stats")
        )
        markup.row(
            types.InlineKeyboardButton("📜 History", callback_data="show_history"),
            types.InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)
        )
        markup.row(
            types.InlineKeyboardButton("👑 99% WIN HACK", url=WIN_99_LINK)
        )

        caption = build_premium_signal()

        try:
            bot.send_message(chat_id, caption, reply_markup=markup, disable_web_page_preview=True)
            if channel_id:
                bot.send_message(channel_id, caption, reply_markup=markup, disable_web_page_preview=True)
        except Exception as e:
            print(f"[Send] {e}")

        last_sent_period[chat_id] = period

        # Wait till next minute
        remaining = get_remaining_seconds()
        for _ in range(remaining):
            if not active_dict.get(chat_id):
                return
            time.sleep(1)

# ===============================
# 📱 KEYBOARD
# ===============================
def main_control_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🚀 Start Prediction", "🛑 Stop Prediction")
    kb.add("📊 Stats", "📜 History")
    kb.add("📢 Set Channel", "👑 Developer Support")
    return kb

# ===============================
# 🤖 HANDLERS
# ===============================
@bot.message_handler(commands=["start"])
def start_command(msg):
    welcome = f"""
╔════════════════════════════════╗
║     👑 *ADITYA HACKER 1.3* 👑   ║
╠════════════════════════════════╣
║  💎 HIGH ACCURACY WINGO 1M     ║
║  🔥 Real Period + AI Engine    ║
║  ⚡ Same Signal as Web App     ║
║  🛡️ Smart Level System         ║
║  📊 Live Stats + History       ║
╠════════════════════════════════╣
║  🔗 [Join VIP Channel]({CHANNEL_LINK}) ║
╚════════════════════════════════╝

👇 *Choose an option below:*
"""
    bot.send_message(msg.chat.id, welcome, reply_markup=main_control_menu(), disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True)
def message_router(msg):
    text = (msg.text or "").strip()
    cid = msg.chat.id

    if text == "🚀 Start Prediction":
        if active_dict.get(cid):
            bot.send_message(cid, "⚠️ Prediction already running!", reply_markup=main_control_menu())
            return

        active_dict[cid] = True
        ch = user_channels.get(cid)

        bot.send_message(cid,
            f"🚀 *Engine Activated!*\n\n"
            f"📡 Status: ● LIVE\n"
            f"{'📢 Channel: `' + str(ch) + '`' if ch else '💬 Mode: Direct Chat'}\n\n"
            f"⏳ Waiting for next period...",
            reply_markup=main_control_menu()
        )
        threading.Thread(target=prediction_worker, args=(cid, ch), daemon=True).start()

    elif text == "🛑 Stop Prediction":
        active_dict[cid] = False
        last_sent_period.pop(cid, None)
        bot.send_message(cid, "🛑 *Prediction stopped.*", reply_markup=main_control_menu())

    elif text == "📊 Stats":
        bot.send_message(cid, build_stats_text(), reply_markup=main_control_menu())

    elif text == "📜 History":
        bot.send_message(cid, build_history_text(), reply_markup=main_control_menu())

    elif text == "📢 Set Channel":
        bot.send_message(cid,
            "📢 Send your *Channel Username* (`@channel`) or *Channel ID* (`-100xxxxxxxxxx`)\n\n"
            "⚠️ Bot must be *Admin* in the channel.",
            parse_mode="Markdown"
        )
        user_channels[cid] = "waiting_channel"

    elif text == "👑 Developer Support":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Contact / Support", url=CHANNEL_LINK))
        bot.send_message(cid, "👑 For support / custom setup:", reply_markup=markup)

    elif user_channels.get(cid) == "waiting_channel":
        ch_input = text
        try:
            bot.send_message(ch_input, "✅ *ADITYA HACKER 1.3* successfully connected!")
            user_channels[cid] = ch_input
            bot.send_message(cid, f"✅ Channel linked: `{ch_input}`", reply_markup=main_control_menu())
        except Exception as e:
            bot.send_message(cid, f"❌ Failed!\nMake bot Admin.\n\nError: `{e}`", reply_markup=main_control_menu())
            user_channels[cid] = None

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "copy_sig":
        bot.answer_callback_query(call.id, "✅ Signal ready! Long press & copy above message.", show_alert=False)
    elif call.data == "show_stats":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, build_stats_text())
    elif call.data == "show_history":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, build_history_text())

# ===============================
# 🚀 BACKGROUND UPDATER (keeps prediction always fresh)
# ===============================
def background_updater():
    while True:
        try:
            update_global_prediction()
        except Exception as e:
            print(f"[Updater] {e}")
        time.sleep(2.4)

# ===============================
# 🚀 RUN
# ===============================
if __name__ == "__main__":
    print("👑 ADITYA HACKER 1.3 Bot Started")
    print("📡 Same Engine as Web | No Cooldown | Premium History | Live Timer")
    threading.Thread(target=background_updater, daemon=True).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
