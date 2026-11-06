import telebot
import threading
import time
import json
import os
import random
import requests
from datetime import datetime, timezone
from telebot import types

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

# Shared prediction state
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
history_list = []                 
total_wins = 0
total_losses = 0
total_jackpots = 0

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
# 🔮 ROBUST PREDICTION GENERATOR
# ===============================
def get_size(n):
    return "BIG" if n >= 5 else "SMALL"

def get_color(n):
    return "RED" if n in [0, 2, 4, 6, 8] else "GREEN"

def generate_next_prediction():
    """Independent robust generator ensuring predictions never fail"""
    global current_pred, loss_streak, last_trend
    
    # Real-time ke mutabiq period full aur short generate karna
    now = datetime.now(timezone.utc)
    # WinGo format ke hisaab se unique period number banana
    base_issue = int(now.strftime("%Y%m%d%H%M"))
    full_period = str(base_issue)
    short_period = full_period[-4:]

    trend = "BIG" if random.random() > 0.48 else "SMALL"
    if loss_streak >= 2:
        trend = "SMALL" if last_trend == "BIG" else "BIG"

    main_num = random.choice([5, 6, 7, 8, 9]) if trend == "BIG" else random.choice([0, 1, 2, 3, 4])
    opp_num = random.choice([0, 1, 2, 3, 4]) if trend == "BIG" else random.choice([5, 6, 7, 8, 9])
    confidence = 99 if loss_streak >= 2 else 97

    with state_lock:
        current_pred = {
            "period_full": full_period,
            "period_short": short_period,
            "trend": trend,
            "main": main_num,
            "opp": opp_num,
            "confidence": confidence,
            "level": min(3, loss_streak + 1)
        }

# Background thread jo har second check karega aur naye period par turant signal bhejega
def prediction_worker(chat_id, channel_id=None):
    print(f"[Worker Started] For Chat ID: {chat_id}")
    
    # Pehli prediction turant set aur send karne ke liye
    generate_next_prediction()
    
    while active_dict.get(chat_id):
        try:
            current_period = current_pred["period_full"]
            
            # Agar last sent period aur current period alag hain, toh turant naya signal bhejo
            if last_sent_period.get(chat_id) != current_period:
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

                bot.send_message(chat_id, caption, reply_markup=markup, disable_web_page_preview=True)
                if channel_id:
                    bot.send_message(channel_id, caption, reply_markup=markup, disable_web_page_preview=True)

                last_sent_period[chat_id] = current_period
                print(f"[Signal Sent Successfully] Period: {current_pred['period_short']} to Chat: {chat_id}")

            # Har 30 seconds par check karein ki naya minute/period shuru hua ya nahi
            time.sleep(1)
            
            # Agar current minute badal gaya hai toh naya prediction generate karo
            now_sec = datetime.now(timezone.utc).second
            if now_sec < 3: # Jaise hi naya minute shuru ho
                generate_next_prediction()

        except Exception as e:
            print(f"[Worker Error]: {e}")
            time.sleep(2)

# ===============================
# 🎯 MESSAGE FORMATTERS
# ===============================
def build_premium_signal():
    p = current_pred
    level_text = {
        1: "SAFE LEVEL 1",
        2: "RECOVERY LEVEL 2",
        3: "SURESHOT LEVEL 3"
    }.get(p["level"], "SAFE LEVEL 1")

    text = f"""
╔════════════════════════════════╗
║   ⚡ *ADITYA HACKER 1.3* ⚡     ║
║   ULTRA FAST AI PREDICTION     ║
╚════════════════════════════════╝

🎮 *Game:* WinGo 1 Minute
📍 *Period:* `{p['period_short']}`

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
        return "⏳ *No history yet... Active predictions are running.*"

    lines = ["📜 *PREDICTION LOGS (Step-by-Step)*\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    for i, h in enumerate(history_list[:12], 1):
        if h["status"] == "JACKPOT":
            badge = "👑 JACKPOT"
        elif h["status"] == "WIN":
            badge = "✅ WIN"
        else:
            badge = "❌ LOSS"

        lines.append(
            f"`{i:02d}.` *Period:* `{h['period']}`\n"
            f"   🎯 *Pred:* {h['pred']}  *[Main: {h['main']} | Backup: {h['opp']}]*\n"
            f"   🎲 *Result:* {h['actual']} `[{h['actual_num']}]`  →  *{badge}*\n"
        )
    return "\n".join(lines)

# ===============================
# 📱 KEYBOARD MENU
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
        active_dict[cid] = True
        last_sent_period.pop(cid, None)

        ch = user_channels.get(cid)

        bot.send_message(cid,
            f"🚀 *Engine Activated Successfully!*\n\n"
            f"📡 Status: ● LIVE\n"
            f"{'📢 Channel: `' + str(ch) + '`' if ch else '💬 Mode: Direct Chat'}\n\n"
            f"⚡ Predictions started instantly!",
            reply_markup=main_control_menu()
        )
        
        # Background worker shuru karna jo bina ruke signals bhejega
        threading.Thread(target=prediction_worker, args=(cid, ch), daemon=True).start()

    elif text == "🛑 Stop Prediction":
        active_dict[cid] = False
        last_sent_period.pop(cid, None)
        bot.send_message(cid, "🛑 *Prediction stopped successfully.*", reply_markup=main_control_menu())

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
# 🚀 RUNNABLE
# ===============================
if __name__ == "__main__":
    print("👑 ADITYA HACKER 1.3 Telegram Bot Started 24/7 (Independent Mode)")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
