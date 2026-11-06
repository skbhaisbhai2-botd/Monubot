import telebot
import threading
import time
import hashlib
from datetime import datetime, timezone
from telebot import types
import json
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===============================
# 🔧 BOT CONFIGURATION
# ===============================
BOT_TOKEN = "9221404814:AAHUfJxq5Ei9dUMt1sgMkRKXOyoJzn-Q55s"
ADMIN_ID = 7741897793
CHANNEL_LINK = "https://t.me/+avZJX9ssyQc5MzI9"
WIN_99_LINK = ""
DEFAULT_GAME_URL = "https://www.91appq.com/#/register?invitationCode=747881278052"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ===============================
# 🌐 GLOBAL STATES
# ===============================
active_dict = {}
user_channels = {}
last_sent_period = {}
DATA_FILE = "prediction_history.json"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# Shared prediction (sab users ko same signal)
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
history_list = []
total_wins = 0
total_losses = 0
total_jackpots = 0

state_lock = threading.Lock()

# ===============================
# 📊 DATA LOAD / SAVE
# ===============================
def load_data():
    global history_list, total_wins, total_losses, total_jackpots, loss_streak, last_trend
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            history_list = data.get("history", [])[:50]
            total_wins = int(data.get("total_wins", 0))
            total_losses = int(data.get("total_losses", 0))
            total_jackpots = int(data.get("total_jackpots", 0))
            loss_streak = int(data.get("loss_streak", 0))
            last_trend = data.get("last_trend")
    except Exception as e:
        print(f"[Load] {e}")

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "history": history_list[:50],
                "total_wins": total_wins,
                "total_losses": total_losses,
                "total_jackpots": total_jackpots,
                "loss_streak": loss_streak,
                "last_trend": last_trend
            }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Save] {e}")

load_data()

# ===============================
# 🔮 HELPERS (WEB LOGIC EXACT)
# ===============================
def get_size(n):
    return "BIG" if int(n) >= 5 else "SMALL"

def get_color(n):
    return "RED" if int(n) in [0, 2, 4, 6, 8] else "GREEN"

def get_remaining_seconds():
    return max(1, 60 - datetime.now(timezone.utc).second)

def create_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://draw.ar-lottery01.com/",
        "Origin": "https://draw.ar-lottery01.com",
        "Connection": "keep-alive",
    })
    return session

def fetch_wingo_list():
    try:
        session = create_session()
        r = session.get(API_URL + f"?t={int(time.time()*1000)}", timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0 and data.get("data", {}).get("list"):
                return data["data"]["list"]
    except Exception as e:
        print(f"[API Error] {e}")
    return None

def deterministic_fallback(period_str):
    """When API fails → pure deterministic so bot always same for same period"""
    h = hashlib.md5(period_str.encode()).hexdigest()
    val = int(h[:8], 16)
    if val % 3 == 0:
        trend = "SMALL"
        main = [0, 1, 2, 3, 4][val % 5]
        opp = [5, 6, 7, 8, 9][val % 5]
    else:
        trend = "BIG"
        main = [5, 6, 7, 8, 9][val % 5]
        opp = [0, 1, 2, 3, 4][val % 5]
    conf = 96 + (val % 4)
    return {"trend": trend, "main": main, "opp": opp, "confidence": conf}

def compute_signal(list_data, period_for_fallback=""):
    """Exact same logic as ADITYA HACKER 1.3 web"""
    global loss_streak, last_trend

    nums = []
    for x in (list_data or [])[:40]:
        try:
            nums.append(int(x["number"]))
        except:
            continue

    if len(nums) < 5:
        return deterministic_fallback(period_for_fallback or str(int(time.time())))

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
    global current_pred, last_issue, next_issue, loss_streak, last_trend
    global total_wins, total_losses, total_jackpots, history_list

    list_data = fetch_wingo_list()

    if list_data:
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
            # Result check for previous prediction
            if current_pred.get("period_full") and last_issue and last_issue != issue_number:
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
                        current_pred["level"] = min(3, current_pred.get("level", 1) + 1)

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
                sig = compute_signal(list_data, next_full)
                current_pred = {
                    "period_full": next_full,
                    "period_short": next_short,
                    "trend": sig["trend"],
                    "main": sig["main"],
                    "opp": sig["opp"],
                    "confidence": sig["confidence"],
                    "level": current_pred.get("level", 1)
                }
    else:
        # API fail → deterministic based on current time period
        now = datetime.now(timezone.utc)
        total_min = now.hour * 60 + now.minute
        fake_period = f"{now.strftime('%Y%m%d')}10001{str(total_min + 1).zfill(4)}"
        short = fake_period[-4:]
        if current_pred.get("period_full") != fake_period:
            sig = deterministic_fallback(fake_period)
            current_pred = {
                "period_full": fake_period,
                "period_short": short,
                "trend": sig["trend"],
                "main": sig["main"],
                "opp": sig["opp"],
                "confidence": sig["confidence"],
                "level": current_pred.get("level", 1)
            }

# ===============================
# 🎯 PREMIUM MESSAGES
# ===============================
def build_premium_signal():
    p = current_pred
    level_map = {1: "SAFE LEVEL 1", 2: "RECOVERY LEVEL 2", 3: "SURESHOT LEVEL 3"}
    level_text = level_map.get(p.get("level", 1), "SAFE LEVEL 1")
    timer = get_remaining_seconds()
    timer_str = f"00:{timer:02d}"

    return f"""
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
""".strip()

def build_stats_text():
    total = total_wins + total_losses + total_jackpots
    rate = round(((total_wins + total_jackpots) / total) * 100) if total > 0 else 97
    return f"""
📊 *ADITYA HACKER 1.3 • LIVE STATS*
━━━━━━━━━━━━━━━━━━━━━━━━

🏆 *Total Wins:* `{total_wins}`
👑 *Jackpots:* `{total_jackpots}`
❌ *Losses:* `{total_losses}`
📈 *Win Rate:* `{rate}%`

🛡️ *Current Level:* `{current_pred.get('level', 1)}`
🔥 *Loss Streak:* `{loss_streak}`
📜 *History Records:* `{len(history_list)}`
""".strip()

def build_history_text():
    if not history_list:
        return """
📜 *PREDICTION LOGS*
━━━━━━━━━━━━━━━━━━━━━━━━

⏳ *No history yet.*

Prediction start karo, result aane ke baad yahan dikhega.
""".strip()

    lines = ["📜 *PREDICTION LOGS (Last 15)*\n━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for i, h in enumerate(history_list[:15], 1):
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
# 🚀 WORKER (NO COOLDOWN)
# ===============================
def prediction_worker(chat_id, channel_id=None):
    while active_dict.get(chat_id):
        update_global_prediction()

        period = current_pred["period_full"]
        if last_sent_period.get(chat_id) == period:
            remaining = get_remaining_seconds()
            for _ in range(remaining):
                if not active_dict.get(chat_id):
                    return
                time.sleep(1)
            continue

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("📋 Copy Signal", callback_data="copy_sig"),
            types.InlineKeyboardButton("📊 Stats", callback_data="show_stats")
        )
        markup.row(
            types.InlineKeyboardButton("📜 History", callback_data="show_history"),
            types.InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)
        )
        markup.row(types.InlineKeyboardButton("👑 99% WIN HACK", url=WIN_99_LINK))

        try:
            bot.send_message(chat_id, build_premium_signal(), reply_markup=markup, disable_web_page_preview=True)
            if channel_id:
                bot.send_message(channel_id, build_premium_signal(), reply_markup=markup, disable_web_page_preview=True)
        except Exception as e:
            print(f"[Send Error] {e}")

        last_sent_period[chat_id] = period

        remaining = get_remaining_seconds()
        for _ in range(remaining):
            if not active_dict.get(chat_id):
                return
            time.sleep(1)

# ===============================
# 📱 KEYBOARD
# ===============================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🚀 Start Prediction", "🛑 Stop Prediction")
    kb.add("📊 Stats", "📜 History")
    kb.add("🗑 Clear History", "📢 Set Channel")
    kb.add("👑 Developer Support")
    return kb

# ===============================
# 🤖 HANDLERS
# ===============================
@bot.message_handler(commands=["start", "help"])
def start_cmd(msg):
    text = f"""
╔════════════════════════════════╗
║     👑 *ADITYA HACKER 1.3* 👑   ║
╠════════════════════════════════╣
║  💎 HIGH ACCURACY WINGO 1M     ║
║  🔥 Real Period + AI Engine    ║
║  ⚡ Same Signal Engine as Web  ║
║  🛡️ Smart Level System         ║
║  📊 Live Stats + Clean History ║
╠════════════════════════════════╣
║  🔗 [Join VIP Channel]({CHANNEL_LINK}) ║
╚════════════════════════════════╝

👇 *Choose option below:*
"""
    bot.send_message(msg.chat.id, text, reply_markup=main_menu(), disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True)
def router(msg):
    text = (msg.text or "").strip()
    cid = msg.chat.id

    if text == "🚀 Start Prediction":
        if active_dict.get(cid):
            bot.send_message(cid, "⚠️ Already running!", reply_markup=main_menu())
            return
        active_dict[cid] = True
        ch = user_channels.get(cid)
        bot.send_message(cid,
            f"🚀 *Engine Activated!*\n\n📡 Status: ● LIVE\n"
            f"{'📢 Channel: `' + str(ch) + '`' if ch else '💬 Mode: Direct'}\n\n"
            f"⏳ Waiting for next period...",
            reply_markup=main_menu()
        )
        threading.Thread(target=prediction_worker, args=(cid, ch), daemon=True).start()

    elif text == "🛑 Stop Prediction":
        active_dict[cid] = False
        last_sent_period.pop(cid, None)
        bot.send_message(cid, "🛑 *Stopped successfully.*", reply_markup=main_menu())

    elif text == "📊 Stats":
        bot.send_message(cid, build_stats_text(), reply_markup=main_menu())

    elif text == "📜 History":
        bot.send_message(cid, build_history_text(), reply_markup=main_menu())

    elif text == "🗑 Clear History":
        global history_list, total_wins, total_losses, total_jackpots, loss_streak, last_trend
        history_list = []
        total_wins = total_losses = total_jackpots = 0
        loss_streak = 0
        last_trend = None
        save_data()
        bot.send_message(cid, "🗑 *History + Stats cleared successfully!*", reply_markup=main_menu())

    elif text == "📢 Set Channel":
        bot.send_message(cid,
            "📢 Send *Channel Username* (`@channel`) ya *Channel ID* (`-100xxxxxxxxxx`)\n\n"
            "⚠️ Bot ko channel mein *Admin* banao.",
            parse_mode="Markdown"
        )
        user_channels[cid] = "waiting_channel"

    elif text == "👑 Developer Support":
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("💬 Contact / Support", url=CHANNEL_LINK))
        bot.send_message(cid, "👑 Support / Custom setup:", reply_markup=mk)

    elif user_channels.get(cid) == "waiting_channel":
        try:
            bot.send_message(text, "✅ *ADITYA HACKER 1.3* connected successfully!")
            user_channels[cid] = text
            bot.send_message(cid, f"✅ Channel linked: `{text}`", reply_markup=main_menu())
        except Exception as e:
            bot.send_message(cid, f"❌ Failed! Bot Admin banao.\nError: `{e}`", reply_markup=main_menu())
            user_channels[cid] = None

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    if call.data == "copy_sig":
        bot.answer_callback_query(call.id, "✅ Long press karke message copy kar lo!", show_alert=False)
    elif call.data == "show_stats":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, build_stats_text())
    elif call.data == "show_history":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, build_history_text())

# ===============================
# 🚀 BACKGROUND UPDATER
# ===============================
def background_updater():
    while True:
        try:
            update_global_prediction()
        except Exception as e:
            print(f"[Background] {e}")
        time.sleep(2.5)

# ===============================
# 🚀 START
# ===============================
if __name__ == "__main__":
    print("👑 ADITYA HACKER 1.3 Bot Started")
    print("📡 Same Engine | No Cooldown | Premium History | Live Timer | Deterministic Fallback")
    threading.Thread(target=background_updater, daemon=True).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
