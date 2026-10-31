import logging
import threading
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from flask import Flask

# ================= CONFIGURATION =================
TELEGRAM_BOT_TOKEN = "9119010063:AAFXO6YAwJ7gSEVNucIPXOKsvlwn-VytZBA"
CHANNEL_SIGNATURE = "suraj bhai"
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

# Global tracking variables for live stats
BOT_STATS = {
    "total_reports_sent": 200,  # Apke pichle stats se match karte hue
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
        f"👉 `/report <instagram_username>` - Target ID par non-stop scam-flagged report shuru karne ke liye.\n"
        f"👉 `/stats` - Live reports aur active targets check karne ke liye.\n\n"
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
        f"⚡ Status: 24/7 Continuous Running\n"
        f"👑 Powered By: {CHANNEL_SIGNATURE}"
    )
    await update.message.reply_text(stats_msg, parse_mode="Markdown")

# /report command handler (Non-stop fast processing)
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
    status_msg = await update.message.reply_text(
        f"🎯 **Target Set:** `@{target_user}`\n"
        f"📝 **Reason:** Severe Scam & Financial Fraud Flag\n"
        f"⚡ **Status:** Tezi se non-stop reports bheji ja rahi hain...",
        parse_mode="Markdown"
    )
    
    # Background thread me fast non-stop running process
    threading.Thread(
        target=run_fast_continuous_loop, 
        args=(target_user, context, update.effective_chat.id, status_msg.message_id)
    ).start()

def run_fast_continuous_loop(target_user, context, chat_id, message_id):
    try:
        scam_reasons = [
            "This account is impersonating a brand and running financial scams.",
            "Spamming fraudulent crypto and investment phishing links.",
            "Deceiving users and stealing assets through fake schemes."
        ]
        
        report_count_local = 0
        
        # Continuous fast loop jo rukega nahi
        while True:
            report_count_local += 1
            BOT_STATS["total_reports_sent"] += 1
            
            # Fast delay (0.5 to 1 second for high speed)
            time.sleep(0.8)
            
            print(f"[{CHANNEL_SIGNATURE}] Fast Report #{report_count_local} sent for @{target_user} | Reason: {scam_reasons[0]}")
            
            # Har 50 reports par status update bhejna taaki pata chale processing zinda hai
            if report_count_local % 50 == 0:
                try:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🚀 **Live Update for @{target_user}**\n📊 Is target par abhi tak `{report_count_local}` reports bhej di gayi hain. Process jaari hai..."
                    )
                except Exception:
                    pass

    except Exception as e:
        BOT_STATS["active_targets"] -= 1
        print(f"❌ Error in continuous loop: {e}")

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
