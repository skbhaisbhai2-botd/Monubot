import os
import io
import base64
import hashlib
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# ======================== CONFIG ========================
BOT_TOKEN = "9248131487:AAFU9cy1CySIDXyxzoFEXDBMInkvO6VS3wc"          # Bot Token added

# Conversation states
WAITING_PASSWORD_ENCRYPT = 1
WAITING_PASSWORD_DECRYPT = 2
WAITING_FILE_ENCRYPT = 3
WAITING_FILE_DECRYPT = 4

# ======================== LOGGING ========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======================== CRYPTO FUNCTIONS ========================

def derive_key(password: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA256 key derivation"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,                          # AES-256
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_data(plaintext: bytes, password: str) -> bytes:
    """
    Encrypt with AES-256-GCM
    Output format:  salt (16) + nonce (12) + ciphertext+tag
    """
    salt = os.urandom(16)
    key = derive_key(password, salt)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return salt + nonce + ciphertext


def decrypt_data(encrypted: bytes, password: str) -> bytes:
    """Decrypt AES-256-GCM data"""
    if len(encrypted) < 28:
        raise ValueError("Invalid encrypted data")
    salt = encrypted[:16]
    nonce = encrypted[16:28]
    ciphertext = encrypted[28:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


# ======================== BOT HANDLERS ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🔒 ENCRYPT HTML", callback_data="encrypt"),
            InlineKeyboardButton("🔓 DECRYPT HTML", callback_data="decrypt"),
        ],
        [InlineKeyboardButton("ℹ️ HELP", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 <b>ADITYA RAJPUT ENCRYPTOR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "AES-256-GCM + PBKDF2 Protected\n\n"
        "• HTML files को password से lock करो\n"
        "• 1 second में decrypt करो\n"
        "• Strong military-grade encryption\n\n"
        "नीचे से option चुनो 👇"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "encrypt":
        await query.edit_message_text(
            "🔒 <b>ENCRYPT MODE</b>\n\n"
            "अब password भेजो (जो file unlock करने के लिए लगेगा):\n\n"
            "Example: <code>846176</code>",
            parse_mode="HTML"
        )
        return WAITING_PASSWORD_ENCRYPT

    elif query.data == "decrypt":
        await query.edit_message_text(
            "🔓 <b>DECRYPT MODE</b>\n\n"
            "अब password भेजो (जिससे file encrypt हुई थी):\n\n"
            "Example: <code>846176</code>",
            parse_mode="HTML"
        )
        return WAITING_PASSWORD_DECRYPT

    elif query.data == "help":
        help_text = (
            "📖 <b>HELP - ADITYA RAJPUT BOT</b>\n\n"
            "<b>ENCRYPT:</b>\n"
            "1. ENCRYPT बटन दबाओ\n"
            "2. Password भेजो\n"
            "3. HTML file भेजो\n"
            "4. Encrypted file मिल जाएगी\n\n"
            "<b>DECRYPT:</b>\n"
            "1. DECRYPT बटन दबाओ\n"
            "2. Password भेजो\n"
            "3. Encrypted file भेजो\n"
            "4. Original HTML मिल जाएगी\n\n"
            "🛡️ Encryption: AES-256-GCM\n"
            "🔑 Key Derivation: PBKDF2 (100k iterations)\n\n"
            "Made with ❤️ by <b>ADITYA RAJPUT</b>"
        )
        await query.edit_message_text(help_text, parse_mode="HTML")
        return ConversationHandler.END


async def receive_password_encrypt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    if len(password) < 4:
        await update.message.reply_text("❌ Password कम से कम 4 characters का होना चाहिए। फिर से भेजो।")
        return WAITING_PASSWORD_ENCRYPT

    context.user_data["password"] = password
    await update.message.reply_text(
        f"✅ Password set: <code>{password}</code>\n\n"
        "अब अपनी <b>HTML file</b> भेजो 📄",
        parse_mode="HTML"
    )
    return WAITING_FILE_ENCRYPT


async def receive_password_decrypt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    if len(password) < 4:
        await update.message.reply_text("❌ Password कम से कम 4 characters का होना चाहिए। फिर से भेजो।")
        return WAITING_PASSWORD_DECRYPT

    context.user_data["password"] = password
    await update.message.reply_text(
        f"✅ Password set: <code>{password}</code>\n\n"
        "अब <b>Encrypted file</b> भेजो 🔒",
        parse_mode="HTML"
    )
    return WAITING_FILE_DECRYPT


async def receive_file_encrypt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("❌ कृपया एक file भेजो (HTML recommended)")
        return WAITING_FILE_ENCRYPT

    password = context.user_data.get("password")
    if not password:
        await update.message.reply_text("❌ Password missing. /start से शुरू करो।")
        return ConversationHandler.END

    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()

    try:
        encrypted = encrypt_data(bytes(file_bytes), password)
        
        # Save as .encrypted
        original_name = update.message.document.file_name or "file.html"
        enc_name = original_name.rsplit(".", 1)[0] + "_encrypted.bin"

        await update.message.reply_document(
            document=InputFile(io.BytesIO(encrypted), filename=enc_name),
            caption=(
                f"✅ <b>AES-256-GCM Encryption Successful!</b>\n\n"
                f"📁 File: <code>{enc_name}</code>\n"
                f"📦 Size: {len(encrypted)/1024:.1f} KB\n"
                f"🔑 Password: <code>{password}</code>\n\n"
                f"🛡️ Protected with:\n"
                f"• AES-256-GCM Encryption\n"
                f"• PBKDF2 Hash Derivation\n"
                f"• Random Salt + Nonce\n\n"
                f"<b>Made by ADITYA RAJPUT</b>"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Encryption failed: {str(e)}")

    context.user_data.clear()
    return ConversationHandler.END


async def receive_file_decrypt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("❌ कृपया encrypted file भेजो")
        return WAITING_FILE_DECRYPT

    password = context.user_data.get("password")
    if not password:
        await update.message.reply_text("❌ Password missing. /start से शुरू करो।")
        return ConversationHandler.END

    file = await update.message.document.get_file()
    encrypted_bytes = await file.download_as_bytearray()

    try:
        decrypted = decrypt_data(bytes(encrypted_bytes), password)

        original_name = update.message.document.file_name or "decrypted"
        if original_name.endswith("_encrypted.bin"):
            out_name = original_name.replace("_encrypted.bin", "_decrypted.html")
        else:
            out_name = original_name.rsplit(".", 1)[0] + "_decrypted.html"

        await update.message.reply_document(
            document=InputFile(io.BytesIO(decrypted), filename=out_name),
            caption=(
                f"✅ <b>Decryption Successful!</b>\n\n"
                f"📁 File: <code>{out_name}</code>\n"
                f"📦 Size: {len(decrypted)/1024:.1f} KB\n"
                f"🔑 Password used: <code>{password}</code>\n\n"
                f"<b>Made by ADITYA RAJPUT</b>"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Decryption Failed!\n\n"
            f"Possible reasons:\n"
            f"• Wrong password\n"
            f"• File corrupted\n"
            f"• Not a valid AES-GCM encrypted file\n\n"
            f"Error: <code>{str(e)}</code>",
            parse_mode="HTML"
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled. /start से फिर शुरू करो।")
    return ConversationHandler.END


# ======================== MAIN ========================

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Bot Token set करो!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(button_handler),
        ],
        states={
            WAITING_PASSWORD_ENCRYPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password_encrypt)
            ],
            WAITING_PASSWORD_DECRYPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password_decrypt)
            ],
            WAITING_FILE_ENCRYPT: [
                MessageHandler(filters.Document.ALL, receive_file_encrypt)
            ],
            WAITING_FILE_DECRYPT: [
                MessageHandler(filters.Document.ALL, receive_file_decrypt)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))

    print("🚀 ADITYA RAJPUT Encryptor Bot Started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
