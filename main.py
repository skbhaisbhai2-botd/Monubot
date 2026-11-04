import os
import io
import logging
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ======================== CONFIG ========================
BOT_TOKEN = "9192618748:AAHFPOL9fYaGWwH48fGElH6khTD-s0jZlTo"

# ======================== CONVERSATION STATES ========================
PAYMENT_PROOF, GAME_UID, GAME_LINK, PROCESSING = range(4)

# ======================== LOGGING ========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======================== RENDER WEB PORT FIX ========================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# ======================== BOT HANDLERS ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔═════════════════════════╗\n"
        "     🌟 **VIP GAMING TOOL PORTAL** 🌟     \n"
        "╚═════════════════════════╝\n\n"
        "⚡ **Advanced Automated Setup System**\n\n"
        "💎 **Step 1 of 3:**\n"
        "Kripya apne **Payment Proof ka Screenshot** yahan chat mein upload karein."
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return PAYMENT_PROOF

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Kripya valid payment screenshot image bhejein!")
        return PAYMENT_PROOF

    await update.message.reply_text(
        "✅ **Payment Screenshot Received Successfully!**\n\n"
        "💎 **Step 2 of 3:**\n"
        "Ab apna **Game UID** enter karein:",
        parse_mode="Markdown"
    )
    return GAME_UID

async def receive_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_uid = update.message.text.strip()
    context.user_data['game_uid'] = user_uid

    await update.message.reply_text(
        f"✅ **Game UID Saved:** `{user_uid}`\n\n"
        "💎 **Step 3 of 3:**\n"
        "Ab apna **Game Link / Profile Link** bhejein:",
        parse_mode="Markdown"
    )
    return GAME_LINK

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_link = update.message.text.strip()
    context.user_data['game_link'] = game_link

    # Start Progress Simulation
    msg = await update.message.reply_text(
        "🔍 **Initializing Verification...**\n"
        "<code>[░░░░░░░░░░] 0%</code>",
        parse_mode="HTML"
    )

    # Simulate Progress Bar from 0 to 100
    steps = [
        ("<code>[██░░░░░░░░] 25%</code>\n⚡ Connecting to secure servers...", 2),
        ("<code>[█████░░░░░] 50%</code>\n🔄 Verifying Game UID & Payment...", 2),
        ("<code>[████████░░] 80%</code>\n🛡️ Bypassing security layers...", 2),
        ("<code>[██████████] 100%</code>\n✅ <b>SUCCESS! Verification Complete!</b>", 2)
    ]

    for progress_text, delay in steps:
        await asyncio.sleep(delay)
        await msg.edit_text(
            f"🔍 **Processing Details...**\n{progress_text}",
            parse_mode="HTML"
        )

    await asyncio.sleep(1.5)

    # Final Premium 2 Hours Wait Message
    final_text = (
        "╔═════════════════════════╗\n"
        "       🚀 **SYSTEM STATUS: QUEUED** 🚀       \n"
        "╚═════════════════════════╝\n\n"
        "✨ **Aapka hack ready hone mein 2 ghante ka time lagega dost, wait karo!** ✨\n\n"
        "📋 **Session Summary:**\n"
        f"• 👤 UID: <code>{context.user_data.get('game_uid')}</code>\n"
        f"• 🔗 Link: <code>{context.user_data.get('game_link')}</code>\n"
        "• 🕒 Estimated Time: **2 Hours**\n\n"
        "⚠️ *Kripya is dauran koi doosra request na dalein. System automatic deploy ho jayega!*"
    )

    await msg.edit_text(final_text, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Process cancelled. /start daba kar dobara shuru karein.")
    return ConversationHandler.END

# ======================== MAIN ========================

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Bot Token set karo!")
        return

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PAYMENT_PROOF: [MessageHandler(filters.PHOTO, receive_screenshot)],
            GAME_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_uid)],
            GAME_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("🚀 VIP Gaming Setup Bot Started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
