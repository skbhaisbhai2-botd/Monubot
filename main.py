import os
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

# ====================== TOKEN YAHAN DALO ======================
BOT_TOKEN = "9236973341:AAHsDn5OQ_fyq1gMLGjiUoC07ZXrHknrb_s"
# =============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ====================== PHOTO ENHANCER CLASS ======================
class UltraPhotoEnhancer:
    def __init__(self, image_path: str):
        self.original = Image.open(image_path).convert("RGB")
        self.img = self.original.copy()
        self.cv_img = cv2.cvtColor(np.array(self.img), cv2.COLOR_RGB2BGR)

    def restore_old_photo(self):
        denoised = cv2.fastNlMeansDenoisingColored(self.cv_img, None, 8, 8, 7, 21)
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.8, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        restored = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        kernel = np.array([[0, -0.6, 0], [-0.6, 3.4, -0.6], [0, -0.6, 0]])
        restored = cv2.filter2D(restored, -1, kernel)
        self.cv_img = restored
        self.img = Image.fromarray(cv2.cvtColor(restored, cv2.COLOR_BGR2RGB))
        return self

    def enhance_face_body_color(self, factor=1.25):
        self.img = ImageEnhance.Color(self.img).enhance(factor)
        self.img = ImageEnhance.Contrast(self.img).enhance(1.18)
        self.img = ImageEnhance.Brightness(self.img).enhance(1.08)
        return self

    def enhance_clothes_detail(self):
        self.img = ImageEnhance.Sharpness(self.img).enhance(1.65)
        self.img = self.img.filter(ImageFilter.DETAIL)
        self.img = self.img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        return self

    def cinematic_look(self, intensity=0.75):
        img = np.array(self.img).astype(np.float32) / 255.0
        r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        r = np.clip(r * 1.05 + 0.02, 0, 1)
        g = np.clip(g * 0.98, 0, 1)
        b = np.clip(b * 1.08 - 0.015, 0, 1)
        rows, cols = img.shape[:2]
        X = np.linspace(-1, 1, cols)
        Y = np.linspace(-1, 1, rows)
        X, Y = np.meshgrid(X, Y)
        vignette = 1 - (X**2 + Y**2) * 0.28 * intensity
        vignette = np.clip(vignette, 0.55, 1.0)
        cinematic = np.stack([r, g, b], axis=2) * vignette[:, :, np.newaxis]
        self.img = Image.fromarray(np.clip(cinematic * 255, 0, 255).astype(np.uint8))
        return self

    def upscale(self, target="4k"):
        w, h = self.img.size
        sizes = {"1080p": (1920, 1080), "2k": (2560, 1440), "4k": (3840, 2160)}
        new_w, new_h = sizes.get(target, (3840, 2160))
        ratio = min(new_w / w, new_h / h)
        new_size = (int(w * ratio), int(h * ratio))
        self.img = self.img.resize(new_size, Image.Resampling.LANCZOS)
        self.img = ImageEnhance.Sharpness(self.img).enhance(1.25)
        return self

    def clean_background(self, strength=0.6):
        img = np.array(self.img)
        blurred = cv2.bilateralFilter(img, 9, 55, 55)
        result = cv2.addWeighted(img, 1 - strength * 0.4, blurred, strength * 0.4, 0)
        self.img = Image.fromarray(result)
        return self

    def full_pipeline(self, mode="cinematic", resolution="4k"):
        self.restore_old_photo()
        self.enhance_face_body_color(1.22 if mode != "vintage" else 1.08)
        self.enhance_clothes_detail()
        self.clean_background(0.55)

        if mode == "cinematic":
            self.cinematic_look(0.8)
        elif mode == "vintage":
            self.img = ImageEnhance.Color(self.img).enhance(0.85)
            self.img = ImageOps.autocontrast(self.img, cutoff=1)
        elif mode == "ultra":
            self.img = ImageEnhance.Color(self.img).enhance(1.35)
            self.img = ImageEnhance.Sharpness(self.img).enhance(1.9)
            self.cinematic_look(0.45)

        self.upscale(resolution)
        return self.img


# ====================== BOT HANDLERS ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 **Ultra HD Photo Enhancer Bot**\n\n"
        "Bas photo bhejo, main usko:\n"
        "• Old / phati photo restore karunga\n"
        "• Face + Body color HD banunga\n"
        "• Kapde detail deep karunga\n"
        "• Full Cinematic look dunga\n"
        "• 1080p / 2K / 4K mein upscale karunga\n\n"
        "Photo bhejne ke baad mode choose kar lena."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Sirf photo bhejo.\n"
        "Phir mode choose karo:\n"
        "• Cinematic (recommended)\n"
        "• Ultra Sharp\n"
        "• Vintage Restore\n"
        "• Natural"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    user_id = update.effective_user.id
    input_path = f"temp_{user_id}_input.jpg"
    await file.download_to_drive(input_path)

    context.user_data["input_path"] = input_path

    keyboard = [
        [
            InlineKeyboardButton("🎬 Cinematic 4K", callback_data="cinematic_4k"),
            InlineKeyboardButton("⚡ Ultra 4K", callback_data="ultra_4k"),
        ],
        [
            InlineKeyboardButton("📜 Vintage 4K", callback_data="vintage_4k"),
            InlineKeyboardButton("🌿 Natural 4K", callback_data="natural_4k"),
        ],
        [
            InlineKeyboardButton("🎬 Cinematic 1080p", callback_data="cinematic_1080p"),
            InlineKeyboardButton("⚡ Ultra 1080p", callback_data="ultra_1080p"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Photo mil gayi ✅\nAb mode choose karo:",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    mode, resolution = data.split("_")

    input_path = context.user_data.get("input_path")
    if not input_path or not Path(input_path).exists():
        await query.edit_message_text("Pehle photo bhejo!")
        return

    await query.edit_message_text(f"⏳ Processing... Mode: {mode.upper()} | {resolution.upper()}\nThoda time lagega...")

    try:
        enhancer = UltraPhotoEnhancer(input_path)
        result = enhancer.full_pipeline(mode=mode, resolution=resolution)

        output_path = f"temp_{query.from_user.id}_output.jpg"
        result.save(output_path, quality=95)

        with open(output_path, "rb") as f:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=f,
                caption=f"✅ Enhanced!\nMode: {mode.upper()} | Resolution: {resolution.upper()}"
            )

        # Cleanup
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(e)
        await query.edit_message_text(f"❌ Error: {str(e)}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
