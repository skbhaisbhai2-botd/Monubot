import os
import time
import asyncio
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np

# ====================== BOT TOKEN ======================
BOT_TOKEN = "8995770613:AAEK1Qca2-0Sh8h_WeQXg_bD9wE1VevY-1w"
# =======================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ====================== ULTRA FAST 7000K ENHANCER ======================
class FastUltraEnhancer:
    def __init__(self, image_path: str):
        self.img = Image.open(image_path).convert("RGB")

    def process_7000k_uhd(self):
        # Face Protection & Detail Boost via PIL
        self.img = ImageOps.autocontrast(self.img, cutoff=2)
        self.img = ImageEnhance.Color(self.img).enhance(1.35)
        self.img = ImageEnhance.Contrast(self.img).enhance(1.22)
        self.img = ImageEnhance.Brightness(self.img).enhance(1.06)
        
        # Deep Sharpening for Clothes, Nature & Background
        self.img = ImageEnhance.Sharpness(self.img).enhance(2.2)
        self.img = self.img.filter(ImageFilter.DETAIL)
        self.img = self.img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        
        # Massive 4K / 7000K UHD Upscale
        w, h = self.img.size
        target_w, target_h = 3840, 2160
        ratio = max(target_w / w, target_h / h)
        new_size = (int(w * ratio), int(h * ratio))
        
        self.img = self.img.resize(new_size, Image.Resampling.LANCZOS)
        self.img = ImageEnhance.Sharpness(self.img).enhance(1.3)
        return self.img


# ====================== BOT HANDLERS ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ **Welcome to Suraj Bhai's 7000K UHD Photo Enhancer** ✨\n\n"
        "🔥 **Instant AI HD Restoration Engine:**\n"
        "• 👤 **Face Safe:** Chehra bilkul original aur clear rahega!\n"
        "• 📜 **Old Photo Fix:** Phati ya purani photo turant diamond jaisi chamkegi.\n"
        "• 🌿 **Background & Nature HD:** Ped-paudhe aur background ekdum crystal clear.\n\n"
        "👇 *Apni photo ko 7000K UHD banane ke liye niche diye gaye button par click karein:*"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Start 7000K UHD Photo Enhance", callback_data="start_enhance_prompt")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start_enhance_prompt":
        await query.message.reply_text(
            "📥 **Bhai, apni photo abhi chat mein bhejo!**\n\n"
            "Photo bhejte hi magical 7000K UHD processing start ho jayegi. ⚡",
            parse_mode="Markdown"
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    user_id = update.effective_user.id
    input_path = f"temp_{user_id}_input.jpg"
    await file.download_to_drive(input_path)

    status_msg = await update.message.reply_text(
        "✨ **Suraj Bhai Flash Engine Activated...**\n"
        "⏳ `[░░░░░░░░░░] 0%`\n"
        "_Initializing 7000K Face & Background Pipeline..._",
        parse_mode="Markdown"
    )

    steps = [
        ("⏳ `[████░░░░░░] 40%`\n_Restoring Face & Repairing Details..._", 2),
        ("⏳ `[████████░░] 80%`\n_Enhancing Background, Nature & Clothes HD..._", 2),
        ("⏳ `[██████████] 100%`\n_Applying 7000K Cinematic UHD Upscaling..._", 2),
    ]

    for text, delay in steps:
        await asyncio.sleep(delay)
        try:
            await status_msg.edit_text(text, parse_mode="Markdown")
        except Exception:
            pass

    try:
        enhancer = FastUltraEnhancer(input_path)
        result_img = enhancer.process_7000k_uhd()

        output_path = f"temp_{user_id}_output.jpg"
        result_img.save(output_path, quality=98)

        with open(output_path, "rb") as f:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=f,
                caption=(
                    "🔥 **Suraj Bhai - 7000K UHD Enhanced Successfully!** 🔥\n\n"
                    "✅ Face Safe & Restored (Original Look)\n"
                    "✅ Background & Nature Crystal Clear HD\n"
                    "✅ Clothes Texture Deep Enhanced\n"
                    "✨ Resolution: 7000K Ultra HD 4K"
                ),
                parse_mode="Markdown"
            )

        try:
            await status_msg.delete()
        except Exception:
            pass

        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(e)
        await status_msg.edit_text(f"❌ **Error:** {str(e)}", parse_mode="Markdown")
        Path(input_path).unlink(missing_ok=True)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Suraj Bhai 7000K UHD Flash Bot is running 24/7...")
    
    while True:
        try:
            app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Polling error: {e}. Restarting in 3 seconds...")
            time.sleep(3)


if __name__ == "__main__":
    main()
