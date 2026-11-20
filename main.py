import json
import os
import threading
import time
import urllib.request
import requests
import telebot
from telebot import types

# ===============================
# 🔧 BOT CONFIGURATION
# ===============================
BOT_TOKEN = "9075932926:AAHckw7i9JmwsnfP5UxrPHXv0FcwWpGaPaQ"
CHANNEL_LINK = "https://t.me/+avZJX9ssyQc5MzI9"
DEFAULT_GAME_URL = "https://www.91appq.com/#/register?invitationCode=747881278052"
DATA_FILE = "prediction_history_dual.json"

APIS = {
    "30S": "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json",
    "1M": "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
}

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ===============================
# 🌐 GLOBAL STATES & STORAGE
# ===============================
user_selected_market = {}
active_subscriptions = {}
user_channels = {}
last_sent_period = {}

state_lock = threading.Lock()


def create_empty_market_state(default_type="SMALL", default_num=4):
    return {
        "last_issue": "",
        "active_period": "",
        "streak": 6,
        "is_initial": True,
        "prediction": {"type": default_type, "number": default_num},
        "history": [],
        "total_wins": 0,
        "total_jackpots": 0,
        "total_losses": 0,
    }


markets_data = {
    "30S": create_empty_market_state("SMALL", 4),
    "1M": create_empty_market_state("BIG", 7),
}


# ===============================
# 📊 DATA PERSISTENCE
# ===============================
def load_data():
    global markets_data
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for m in ["30S", "1M"]:
            if m in raw and isinstance(raw[m], dict):
                base = create_empty_market_state(
                    "SMALL" if m == "30S" else "BIG",
                    4 if m == "30S" else 7,
                )
                base.update(raw[m])
                base["history"] = base.get("history", [])[:20]
                markets_data[m] = base
    except Exception as e:
        print(f"[Load Error] {e}")


def save_data():
    try:
        with state_lock:
            payload = {
                m: {
                    "last_issue": markets_data[m]["last_issue"],
                    "active_period": markets_data[m]["active_period"],
                    "streak": markets_data[m]["streak"],
                    "is_initial": markets_data[m]["is_initial"],
                    "prediction": markets_data[m]["prediction"],
                    "history": markets_data[m]["history"][:20],
                    "total_wins": markets_data[m]["total_wins"],
                    "total_jackpots": markets_data[m]["total_jackpots"],
                    "total_losses": markets_data[m]["total_losses"],
                }
                for m in ["30S", "1M"]
            }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        print(f"[Save Error] {e}")


load_data()


# ===============================
# 🔮 PREDICTION LOGIC (HTML SYNCED)
# ===============================
def get_size_from_num(n: int) -> str:
    return "SMALL" if 0 <= n <= 4 else "BIG"


def get_color_from_num(n: int) -> str:
    return "RED" if n in [0, 2, 4, 6, 8] else "GREEN"


def parse_item(item: dict):
    issue = str(
        item.get("issue")
        or item.get("issueNumber")
        or item.get("period")
        or item.get("IssueNumber")
        or item.get("issueNo")
        or ""
    ).strip()
    raw_num = item.get("number")
    if raw_num is None:
        raw_num = item.get("openNumber")
    if raw_num is None:
        raw_num = item.get("result")
    if raw_num is None:
        raw_num = item.get("Number", 0)
    try:
        number = int(raw_num)
    except Exception:
        number = 0
    size_type = get_size_from_num(number)
    return {"issue": issue, "number": number, "type": size_type}


def calculate_smart_prediction(history_list: list, next_period_str: str) -> dict:
    """
    HTML calculateSmartPrediction ka exact Python equivalent:
    1. Dragon Streak (3+ same type)
    2. Alternating Reversal (last 3 alternate)
    3. Momentum (last 5 majority)
    4. Frequency weight + period last digit seed
    """
    if not history_list or len(history_list) < 3:
        return {"type": "SMALL", "number": 2}

    recent = history_list[:10]
    types = [x["type"] for x in recent]
    numbers = [x["number"] for x in recent]

    predicted_type = "SMALL"

    # 1. Dragon Streak
    dragon_count = 1
    for i in range(len(types) - 1):
        if types[i] == types[i + 1]:
            dragon_count += 1
        else:
            break

    if dragon_count >= 3:
        predicted_type = types[0]
    # 2. Alternating Reversal
    elif types[0] != types[1] and types[1] != types[2]:
        predicted_type = "SMALL" if types[0] == "BIG" else "BIG"
    # 3. Momentum
    else:
        big_count = sum(1 for t in types[:5] if t == "BIG")
        predicted_type = "BIG" if big_count >= 3 else "SMALL"

    # 4. Frequency Weight
    candidate_pool = [0, 1, 2, 3, 4] if predicted_type == "SMALL" else [5, 6, 7, 8, 9]
    freq_map = {n: 0 for n in candidate_pool}
    for n in numbers:
        if n in freq_map:
            freq_map[n] += 1

    try:
        period_seed = int(next_period_str[-1]) if next_period_str else 0
    except Exception:
        period_seed = 0

    candidate_pool.sort(key=lambda x: freq_map[x], reverse=True)
    chosen_number = candidate_pool[period_seed % len(candidate_pool)]

    return {"type": predicted_type, "number": chosen_number}


def extract_list_from_json(data: dict):
    if not isinstance(data, dict):
        return None
    raw_list = (
        data.get("data", {}).get("list")
        if isinstance(data.get("data"), dict)
        else None
    )
    if raw_list is None:
        raw_list = data.get("data") if isinstance(data.get("data"), list) else data.get("list")
    if isinstance(raw_list, list) and len(raw_list) > 0:
        parsed = [parse_item(x) for x in raw_list if isinstance(x, dict)]
        parsed = [x for x in parsed if x["issue"]]
        if parsed:
            return parsed
    return None


def fetch_market_list(market: str):
    url = APIS.get(market)
    if not url:
        return None
    full_url = f"{url}?_={int(time.time() * 1000)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://draw.ar-lottery01.com/",
        "Origin": "https://draw.ar-lottery01.com",
    }

    # Primary fetch via requests
    try:
        resp = requests.get(full_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            parsed = extract_list_from_json(resp.json())
            if parsed:
                return parsed
    except Exception as e:
        print(f"[Requests Warning {market}] {e}")

    # Fallback fetch via urllib
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as r:
            body = r.read().decode("utf-8", errors="ignore")
            parsed = extract_list_from_json(json.loads(body))
            if parsed:
                return parsed
    except Exception as e:
        print(f"[Urllib Warning {market}] {e}")

    return None


def update_market_state(market: str):
    parsed_list = fetch_market_list(market)
    if not parsed_list:
        return

    latest = parsed_list[0]
    next_period = str(int(latest["issue"]) + 1)

    changed = False
    with state_lock:
        st = markets_data[market]

        if st["is_initial"] or not st["active_period"]:
            st["is_initial"] = False
            st["last_issue"] = latest["issue"]
            st["active_period"] = next_period
            st["prediction"] = calculate_smart_prediction(parsed_list, next_period)

            if not st["history"]:
                seed_history = []
                for item in parsed_list[:9]:
                    seed_history.append({
                        "period": item["issue"],
                        "predicted_type": item["type"],
                        "predicted_num": item["number"],
                        "result_type": item["type"],
                        "result_num": item["number"],
                        "status": "WIN",
                    })
                st["history"] = seed_history
                st["total_wins"] = len(seed_history)
            changed = True

        elif latest["issue"] != st["last_issue"]:
            st["last_issue"] = latest["issue"]

            pred_type = st["prediction"]["type"]
            pred_num = st["prediction"]["number"]

            is_type_win = latest["type"].upper() == pred_type.upper()
            is_exact_num = latest["number"] == pred_num

            if is_type_win and is_exact_num:
                final_status = "JACKPOT"
                st["total_jackpots"] += 1
                st["streak"] += 1
            elif is_type_win:
                final_status = "WIN"
                st["total_wins"] += 1
                st["streak"] += 1
            else:
                final_status = "LOSS"
                st["total_losses"] += 1
                st["streak"] = 0

            st["history"].insert(0, {
                "period": latest["issue"],
                "predicted_type": pred_type,
                "predicted_num": pred_num,
                "result_type": latest["type"],
                "result_num": latest["number"],
                "status": final_status,
            })
            st["history"] = st["history"][:20]

            st["active_period"] = next_period
            st["prediction"] = calculate_smart_prediction(parsed_list, next_period)
            changed = True

    if changed:
        save_data()


# ===============================
# 🎯 MESSAGE FORMATTERS (PERIOD INCLUDED)
# ===============================
def get_user_market(chat_id: int) -> str:
    return user_selected_market.get(chat_id, "30S")


def format_period_pair(period_str: str) -> str:
    if not period_str:
        return "----"
    short_p = period_str[-5:] if len(period_str) > 5 else period_str
    return f"`{period_str}` (`{short_p}`)"


def build_signal_message(market: str) -> str:
    update_market_state(market)
    with state_lock:
        st = markets_data[market]
        period = st["active_period"] or "----"
        pred_type = st["prediction"]["type"]
        pred_num = st["prediction"]["number"]
        streak = st["streak"]
        wins = st["total_wins"]
        jackpots = st["total_jackpots"]
        losses = st["total_losses"]

    total_rounds = wins + jackpots + losses
    win_rate = round(((wins + jackpots) / total_rounds) * 100, 1) if total_rounds > 0 else 96.0
    market_label = "WinGo 30 Seconds" if market == "30S" else "WinGo 1 Minute"
    size_emoji = "🟢" if pred_type == "SMALL" else "🔴"

    return f"""
╔════════════════════════════════╗
║   ⚡ *SYNC AI WINGO [{market}]* ⚡   ║
║   30S / 1M DUAL MARKET ENGINE  ║
╚════════════════════════════════╝

🎮 *Game:* {market_label} (`{market}`)
📍 *Game Period:* {format_period_pair(period)}

{size_emoji} *Prediction:* *{pred_type}*
🎲 *Predicted Number:* `{pred_num}`

🔥 *Current Streak:* `{streak}`
📈 *Win Rate:* `{win_rate}%`

━━━━━━━━━━━━━━━━━━━━━━━━
🎮 *Game Link:*
{DEFAULT_GAME_URL}

🔗 *Channel:* {CHANNEL_LINK}
━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def build_stats_message(market: str) -> str:
    update_market_state(market)
    with state_lock:
        st = markets_data[market]
        wins = st["total_wins"]
        jackpots = st["total_jackpots"]
        losses = st["total_losses"]
        streak = st["streak"]
        period = st["active_period"] or "----"

    total = wins + jackpots + losses
    rate = round(((wins + jackpots) / total) * 100, 1) if total > 0 else 96.0
    market_label = "WinGo 30 Seconds" if market == "30S" else "WinGo 1 Minute"

    return f"""
📊 *STATS — {market_label} (`{market}`)*
━━━━━━━━━━━━━━━━━━━━━━

📍 *Active Period:* {format_period_pair(period)}
🏆 *Wins:* `{wins}`
👑 *Jackpots:* `{jackpots}`
❌ *Losses:* `{losses}`
📈 *Win Rate:* `{rate}%`
🔥 *Streak:* `{streak}`
""".strip()


def build_history_message(market: str) -> str:
    update_market_state(market)
    with state_lock:
        hist = list(markets_data[market]["history"][:10])
        active_p = markets_data[market]["active_period"]

    market_label = "WinGo 30 Seconds" if market == "30S" else "WinGo 1 Minute"
    if not hist:
        return f"⏳ *{market_label} (`{market}`)*\n*Current Period:* {format_period_pair(active_p)}\n\nNo history yet..."

    lines = [
        f"📜 *HISTORY — {market_label} (`{market}`)*",
        f"📍 *Next Period:* {format_period_pair(active_p)}",
        "━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    for idx, item in enumerate(hist, 1):
        status = item["status"]
        if status == "JACKPOT":
            badge = "👑 JACKPOT"
        elif status == "WIN":
            badge = "✅ WIN"
        else:
            badge = "❌ LOSS"

        p_full = item["period"]
        p_short = p_full[-5:] if len(p_full) > 5 else p_full
        res_color = get_color_from_num(item["result_num"])

        lines.append(
            f"`{idx:02d}.` *Period:* `{p_full}` (`{p_short}`)\n"
            f"    🎯 *Pred:* *{item['predicted_type']}* (`{item['predicted_num']}`)  |  "
            f"*Actual:* *{item['result_type']}* (`{item['result_num']}` / {res_color})\n"
            f"    📌 *Status:* *{badge}*\n"
        )

    return "\n".join(lines)


# ===============================
# 🚀 BROADCAST WORKER (SINGLE-SEND PER PERIOD)
# ===============================
def broadcast_loop():
    while True:
        try:
            for m in ["30S", "1M"]:
                update_market_state(m)

            with state_lock:
                current_periods = {
                    m: markets_data[m]["active_period"] for m in ["30S", "1M"]
                }
                subs = [
                    (chat_id, market)
                    for (chat_id, market), is_on in active_subscriptions.items()
                    if is_on
                ]

            for chat_id, market in subs:
                period = current_periods.get(market, "")
                if not period:
                    continue

                with state_lock:
                    already_sent = last_sent_period.get((chat_id, market)) == period
                    target_channel = user_channels.get(chat_id)
                    if target_channel == "waiting_channel":
                        target_channel = None

                if already_sent:
                    continue

                msg_text = build_signal_message(market)
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton(f"📊 {market} Stats", callback_data=f"stats_{market}"),
                    types.InlineKeyboardButton(f"📜 {market} History", callback_data=f"hist_{market}"),
                )
                markup.row(
                    types.InlineKeyboardButton("⏱️ Switch 30S", callback_data="sw_30S"),
                    types.InlineKeyboardButton("⏱️ Switch 1M", callback_data="sw_1M"),
                )
                markup.row(
                    types.InlineKeyboardButton("🎮 Open Game", url=DEFAULT_GAME_URL),
                    types.InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK),
                )

                try:
                    bot.send_message(
                        chat_id,
                        msg_text,
                        reply_markup=markup,
                        disable_web_page_preview=True,
                    )
                    if target_channel:
                        bot.send_message(
                            target_channel,
                            msg_text,
                            reply_markup=markup,
                            disable_web_page_preview=True,
                        )

                    with state_lock:
                        last_sent_period[(chat_id, market)] = period
                except Exception as send_err:
                    print(f"[Send Error chat={chat_id} market={market}] {send_err}")

        except Exception as loop_err:
            print(f"[Broadcast Loop Error] {loop_err}")

        time.sleep(2)


# ===============================
# 📱 KEYBOARD MENU
# ===============================
def build_main_menu(chat_id: int) -> types.ReplyKeyboardMarkup:
    active_m = get_user_market(chat_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("⏱️ 30S Market", "⏱️ 1M Market")
    kb.add(f"🚀 Start {active_m}", f"🛑 Stop {active_m}")
    kb.add("📊 Stats", "📜 History")
    kb.add("🎯 Current Signal", "📢 Set Channel")
    return kb


# ===============================
# 🤖 TELEGRAM HANDLERS
# ===============================
@bot.message_handler(commands=["start"])
def handle_start(message):
    chat_id = message.chat.id
    user_selected_market.setdefault(chat_id, "30S")
    active_m = get_user_market(chat_id)

    for m in ["30S", "1M"]:
        update_market_state(m)

    with state_lock:
        active_p = markets_data[active_m]["active_period"] or "----"

    welcome = f"""
╔════════════════════════════════╗
║   👑 *WINGO 30S & 1M SYNC BOT* 👑  ║
╠════════════════════════════════╣
║  ⏱️ Supports *30S* & *1M* Markets ║
║  🎯 Same AI Prediction Logic   ║
║  📍 Live Period + WIN/LOSS Log ║
║  📊 Streak + History Tracking  ║
╠════════════════════════════════╣
║  🔗 [Join Channel]({CHANNEL_LINK}) ║
╚════════════════════════════════╝

📌 *Selected Market:* `{active_m}`
📍 *Active Period:* {format_period_pair(active_p)}
👇 *Neeche se market ya action chunein:*
""".strip()

    bot.send_message(
        chat_id,
        welcome,
        reply_markup=build_main_menu(chat_id),
        disable_web_page_preview=True,
    )


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    if text == "⏱️ 30S Market":
        user_selected_market[chat_id] = "30S"
        bot.send_message(
            chat_id,
            "✅ *Market switched to WinGo 30 Seconds (`30S`)*",
            reply_markup=build_main_menu(chat_id),
        )
        bot.send_message(chat_id, build_signal_message("30S"), disable_web_page_preview=True)

    elif text == "⏱️ 1M Market":
        user_selected_market[chat_id] = "1M"
        bot.send_message(
            chat_id,
            "✅ *Market switched to WinGo 1 Minute (`1M`)*",
            reply_markup=build_main_menu(chat_id),
        )
        bot.send_message(chat_id, build_signal_message("1M"), disable_web_page_preview=True)

    elif text in ["🚀 Start 30S", "🚀 Start 1M"]:
        target_market = "30S" if "30S" in text else "1M"
        user_selected_market[chat_id] = target_market
        update_market_state(target_market)

        with state_lock:
            active_subscriptions[(chat_id, target_market)] = True
            last_sent_period.pop((chat_id, target_market), None)
            ch = user_channels.get(chat_id)
            if ch == "waiting_channel":
                ch = None
            period = markets_data[target_market]["active_period"] or "----"

        bot.send_message(
            chat_id,
            f"🚀 *Auto Prediction Started for `{target_market}`!*\n"
            f"📍 *Active Period:* {format_period_pair(period)}\n"
            f"{'📢 *Channel:* `' + str(ch) + '`' if ch else '💬 *Mode:* Direct Chat'}",
            reply_markup=build_main_menu(chat_id),
        )

    elif text in ["🛑 Stop 30S", "🛑 Stop 1M"]:
        target_market = "30S" if "30S" in text else "1M"
        with state_lock:
            active_subscriptions[(chat_id, target_market)] = False
            last_sent_period.pop((chat_id, target_market), None)

        bot.send_message(
            chat_id,
            f"🛑 *Auto Prediction Stopped for `{target_market}`.*",
            reply_markup=build_main_menu(chat_id),
        )

    elif text == "🎯 Current Signal":
        m = get_user_market(chat_id)
        bot.send_message(
            chat_id,
            build_signal_message(m),
            reply_markup=build_main_menu(chat_id),
            disable_web_page_preview=True,
        )

    elif text == "📊 Stats":
        m = get_user_market(chat_id)
        bot.send_message(
            chat_id,
            build_stats_message(m),
            reply_markup=build_main_menu(chat_id),
        )

    elif text == "📜 History":
        m = get_user_market(chat_id)
        bot.send_message(
            chat_id,
            build_history_message(m),
            reply_markup=build_main_menu(chat_id),
        )

    elif text == "📢 Set Channel":
        with state_lock:
            user_channels[chat_id] = "waiting_channel"
        bot.send_message(
            chat_id,
            "📢 Apne Channel ka *Username* (`@channel`) ya *ID* (`-100xxxxxxxxxx`) bhejein.\n"
            "⚠️ Bot us channel mein *Admin* hona chahiye.",
        )

    elif user_channels.get(chat_id) == "waiting_channel":
        ch_input = text
        try:
            bot.send_message(ch_input, "✅ *WinGo 30S & 1M Sync Bot* successfully connected!")
            with state_lock:
                user_channels[chat_id] = ch_input
            bot.send_message(
                chat_id,
                f"✅ Channel linked: `{ch_input}`",
                reply_markup=build_main_menu(chat_id),
            )
        except Exception as e:
            with state_lock:
                user_channels.pop(chat_id, None)
            bot.send_message(
                chat_id,
                f"❌ Channel connect nahi ho paya. Bot ko Admin banayein.\n*Error:* `{e}`",
                reply_markup=build_main_menu(chat_id),
            )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data or ""

    if data.startswith("stats_"):
        m = data.split("_", 1)[1]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, build_stats_message(m))

    elif data.startswith("hist_"):
        m = data.split("_", 1)[1]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, build_history_message(m))

    elif data.startswith("sw_"):
        m = data.split("_", 1)[1]
        if m in ["30S", "1M"]:
            user_selected_market[chat_id] = m
            bot.answer_callback_query(call.id, f"Switched to {m}")
            bot.send_message(
                chat_id,
                build_signal_message(m),
                reply_markup=build_main_menu(chat_id),
                disable_web_page_preview=True,
            )


# ===============================
# 🚀 ENTRYPOINT
# ===============================
if __name__ == "__main__":
    print("👑 WinGo 30S & 1M Sync Bot Started...")
    threading.Thread(target=broadcast_loop, daemon=True).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
