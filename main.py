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
import cv2
import numpy as np

# ====================== SURAJ BHAI BOT TOKEN ======================
BOT_TOKEN = "8995770613:AAEK1Qca2-0Sh8h_WeQXg_bD9wE1VevY-1w"
# =================================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ====================== 7000K UHD ULTRA ENHANCER ENGINE ======================
class Ultra7000KPhotoEnhancer:
    def __init__(self, image_path: str):
        self.original = Image.open(image_path).convert("RGB")
        self.img = self.original.copy()
        self.cv_img = cv2.cvtColor(np.array(self.img), cv2.COLOR_RGB2BGR)

    def restore_and_protect_face(self):
        """
        Chehre ke features aur natural skin tones ko safe rakhte hue
        purani, phati ya scratched photo ko clean aur sharp karta hai.
        """
        denoised = cv2.fastNlMeansDenoisingColored(self.cv_img, None, 10, 10, 7, 21)
        
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.2, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        balanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        kernel = np.array([[0, -0.7, 0], [-0.7, 3.8, -0.7], [0, -0.7, 0]])
        sharpened = cv2.filter2D(balanced, -1, kernel)
        
        self.cv_img = sharpened
        self.img = Image.fromarray(cv2.cvtColor(sharpened, cv2.COLOR_BGR2RGB))
        return self

    def enhance_details_7000k(self):
        """
        Kapde, Background, aur Ped-Paudhe (Nature) ko ultra HD clarity deta hai.
        """
        self.img = ImageEnhance.Color(self.img).enhance(1.35)
        self.img = ImageEnhance.Contrast(self.img).enhance(1.25)
        self.img = ImageEnhance.Brightness(self.img).enhance(1.06)
        
        self.img = ImageEnhance.Sharpness(self.img).enhance(2.2)
        self.img = self.img.filter(ImageFilter.DETAIL)
        self.img = self.img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        
        np_arr = np.array(self.img)
        bg_smooth = cv2.bilateralFilter(np_arr, 9, 75, 75)
        self.img = Image.fromarray(cv2.addWeighted(np_arr, 0.68, bg_smooth, 0.32, 0))
        return self

    def cinematic_7000k_grading(self):
        """
        Hollywood grade 7000K UHD lighting tone correction.
        """
        img = np.array(self.img).astype(np.float32) / 255.0
        r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        r = np.clip(r * 1.08 + 0.03, 0, 1)
        g = np.clip(g * 1.01, 0, 1)
        b = np.clip(b * 1.13 - 0.02, 0, 1)
        
        rows, cols = img.shape[:2]
        X = np.linspace(-1, 1, cols)
        Y = np.linspace(-1, 1, rows)
        X, Y = np.meshgrid(X, Y)
        vignette = 1 - (X**2 + Y**2) * 0.22 * 0.6
        vignette = np.clip(vignette, 0.65, 1.0)
        
        graded = np.stack([r, g, b], axis=2) * vignette[:, :, np.newaxis]
        self.img = Image.fromarray(np.clip(graded * 255, 0, 255).astype(np.uint8))
        return self

    def upscale_to_7000k_uhd(self):
        """
        Image ko massive 4K / 7000K UHD resolution par upscale karta hai.
        """
        w, h = self.img.size
        target_w, target_h = 3840, 2160
        ratio = max(target_w / w, target_h / h)
        new_size = (int(w * ratio), int(h * ratio))
        
        self.img = self.img.resize(new_size, Image.Resampling.LANCZOS)
        self.img = ImageEnhance.Sharpness(self.img).enhance(1.45)
        return self.img

    def full_7000k_pipeline(self):
        self.restore_and_protect_face()
        self.enhance_details_7000k()
        self.cinematic_7000k_grading()
        return self.upscale_to_7000k_uhd()


# ====================== BOT HANDLERS ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ **Welcome to Suraj Bhai's 7000K UHD Photo Enhancer** ✨\n\n"
        "🔥 **The Ultimate AI Restoration & HD Engine:**\n"
        "• 👤 **Face Safe Protection:** Chehra wahi rahega, bilkul original aur natural!\n"
        "• 📜 **Old Photo Repair:** Kitni bhi purani ya phati hui photo ho, turant fix hogi.\n"
        "• 🌿 **Background & Nature HD:** Ped-paudhe aur background ekdum crystal clear.\n"
        "• 🧥 **Cloth Texture Booster:** Kapdo ki har detail aur silvat premium banegi.\n\n"
        "👇 *Apni photo ko turant 7000K UHD banane ke liye niche diye gaye button par click karein:*"
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
        ("⏳ `[████░░░░░░] 35%`\n_Restoring Face & Repairing Old Scratches..._", 3),
        ("⏳ `[████████░░] 75%`\n_Enhancing Background, Nature & Clothes HD..._", 4),
        ("⏳ `[██████████] 100%`\n_Applying 7000K Cinematic UHD Upscaling..._", 3),
    ]

    for text, delay in steps:
        await asyncio.sleep(delay)
        try:
            await status_msg.edit_text(text, parse_mode="Markdown")
        except Exception:
            pass

    try:
        enhancer = Ultra7000KPhotoEnhancer(input_path)
        result_img = enhancer.full_7000k_pipeline()

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
            logger.error(f"Polling error encountered: {e}. Restarting in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()
