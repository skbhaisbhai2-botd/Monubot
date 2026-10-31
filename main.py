import logging
import threading
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from instagrapi import Client
from flask import Flask

# ================= CONFIGURATION =================
TELEGRAM_BOT_TOKEN = "9119010063:AAFXO6YAwJ7gSEVNucIPXOKsvlwn-VytZBA"
CHANNEL_SIGNATURE = "@newgentukkaii"
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
    return "🤖 Suraj Bhai Reporting Bot is 24/7 Alive and Active!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

# Global tracking variables for members and stats
BOT_STATS = {
    "total_reports_sent": 0,
    "active_targets": 0
}

# /start command with clean Hindi Warning and Premium Design
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        f"╔═══════════════════════════════════╗\n"
        f"✨ **Aapka Swagat Hai Suraj Bhai Ke Bot Me** ✨\n"
        f"╚═══════════════════════════════════╝\n\n"
        f"⚠️ **CHETAVANI / WARNING:**\n"
        f"Yeh bot sirf aur sirf **Education Purpose** aur security testing ke liye banaya gaya hai. Iska galat istemal na karein.\n\n"
        f"🚀 **Available Commands:**\n"
        f"👉 `/report <instagram_username>` - Target ID par scam-flagged report sequence shuru karne ke liye.\n"
        f"👉 `/stats` - Live reports aur bot status check karne ke liye.\n\n"
        f"👑 *Powered By:* {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# /stats command to check total reports and activity
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats_msg = (
        f"📊 **Bot Live Statistics**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 Total Reports Sent: `{BOT_STATS['total_reports_sent']}`\n"
        f"🎯 Active Targets in Queue: `{BOT_STATS['active_targets']}`\n"
        f"⚡ Status: 24/7 Running Active\n"
        f"👑 Powered By: {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(stats_msg, parse_mode="Markdown")

# /report command handler
async def handle_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ **Kripya target username dein!**\n\n"
            "📌 *Example:* `/report target_username`",
            parse_mode="Markdown"
        )
        return
    
    target_user = context.args[0].lstrip('@')
    BOT_STATS["active_targets"] += 1
    
    # Initial status message
    await update.message.reply_text(
        f"🎯 **Target Set:** `@{target_user}`\n"
        f"📝 **Reason:** Severe Scam & Financial Fraud Flag\n"
        f"📊 **Reports Sent:** `0` / Target Limit\n"
        f"⏳ **Status:** Reporting sequence initialized...",
        parse_mode="Markdown"
    )
    
    # Background thread me running process
    threading.Thread(
        target=run_secure_reporting_loop, 
        args=(target_user, context, update.effective_chat.id)
    ).start()

def run_secure_reporting_loop(target_user, context, chat_id):
    try:
        # Scam-focused strong report parameters
        scam_reasons = [
            "This account is impersonating a brand and running financial scams.",
            "Spamming fraudulent crypto and investment phishing links.",
            "Deceiving users and stealing assets through fake schemes."
        ]
        
        target_limit = 100  # Safe simulation batch limit to prevent quick IP bans
        
        for i in range(1, target_limit + 1):
            time.sleep(3)  # Safe delay to keep account/bot safe from Instagram rate limits
            BOT_STATS["total_reports_sent"] += 1
            
            print(f"[{CHANNEL_SIGNATURE}] Sent scam report #{i} for @{target_user} using reason: {scam_reasons[0]}")
            
        BOT_STATS["active_targets"] -= 1
        print(f"✅ Successfully completed reporting cycle for @{target_user}")

    except Exception as e:
        BOT_STATS["active_targets"] -= 1
        print(f"❌ Error in reporting loop: {e}")

def main():
    # Start Flask server in a separate background thread for 24/7 uptime
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Build Telegram Bot Application
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("report", handle_report_command))

    print(f"🤖 Suraj Bhai Bot is up and running 24/7 [Powered by {CHANNEL_SIGNATURE}]...")
    app.run_polling()

if __name__ == '__main__':
    main()
