import os
import io
import base64
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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
BOT_TOKEN = "9248131487:AAFU9cy1CySIDXyxzoFEXDBMInkvO6VS3wc"

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

# ======================== RENDER WEB PORT FIX ========================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")
    
    def log_message(self, format, *args):
        pass # Suppress server logs to keep console clean

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()

# ======================== CRYPTO FUNCTIONS ========================

def derive_key(password: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA256 key derivation"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_data(plaintext: bytes, password: str) -> bytes:
    """Encrypt with AES-256-GCM"""
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


def create_encrypted_html(encrypted_bytes: bytes, password: str) -> str:
    """Generate self-decrypting HTML wrapper with copy & inspect protection"""
    enc_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Protected HTML File</title>
    <style>
        body {{
            background: #0f172a;
            color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }}
        .auth-container {{
            background: #1e293b;
            padding: 35px 30px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
            text-align: center;
            width: 340px;
            border: 1px solid #334155;
        }}
        h2 {{ margin-bottom: 10px; color: #38bdf8; font-size: 22px; }}
        p {{ color: #94a3b8; font-size: 14px; margin-bottom: 20px; }}
        input {{
            width: 100%;
            padding: 12px 15px;
            margin-bottom: 15px;
            border: 1px solid #475569;
            background: #0f172a;
            color: #fff;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 16px;
            outline: none;
            transition: border-color 0.2s;
        }}
        input:focus {{ border-color: #38bdf8; }}
        button {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
            font-weight: bold;
            transition: background 0.2s;
        }}
        button:hover {{ background: #1d4ed8; }}
        #error {{ color: #ef4444; margin-top: 12px; font-size: 13px; font-weight: 500; }}
    </style>
</head>
<body oncontextmenu="return false;" onselectstart="return false;" ondragstart="return false;">
    <div class="auth-container">
        <h2>🔒 Secured Page</h2>
        <p>Enter your password to unlock the content:</p>
        <input type="password" id="passwordInput" placeholder="Enter Password" autofocus>
        <button onclick="unlockContent()">Unlock File</button>
        <div id="error"></div>
    </div>

    <script>
        // Block Inspect, View Source & Shortcuts
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C' || e.key === 'J')) || 
                (e.ctrlKey && e.key === 'u')) {{
                e.preventDefault();
                return false;
            }}
        }});

        async function unlockContent() {{
            const password = document.getElementById('passwordInput').value;
            const errorDiv = document.getElementById('error');
            
            if (!password) {{
                errorDiv.innerText = "⚠️ Please enter the password!";
                return;
            }}

            try {{
                errorDiv.innerText = "⏳ Decrypting...";
                const rawData = Uint8Array.from(atob("{enc_b64}"), c => c.charCodeAt(0));
                const salt = rawData.slice(0, 16);
                const iv = rawData.slice(16, 28);
                const ciphertext = rawData.slice(28);

                const enc = new TextEncoder();
                const keyMaterial = await window.crypto.subtle.importKey(
                    "raw", enc.encode(password), {{ name: "PBKDF2" }}, false, ["deriveKey"]
                );
                
                const key = await window.crypto.subtle.deriveKey(
                    {{ name: "PBKDF2", salt: salt, iterations: 100000, hash: "SHA-256" }},
                    keyMaterial,
                    {{ name: "AES-GCM", length: 256 }},
                    false,
                    ["decrypt"]
                );

                const decrypted = await window.crypto.subtle.decrypt(
                    {{ name: "AES-GCM", iv: iv }}, key, ciphertext
                );

                const decoder = new TextDecoder();
                const htmlContent = decoder.decode(decrypted);

                document.open();
                document.write(htmlContent);
                document.close();
            } catch (err) {{
                errorDiv.innerText = "❌ Incorrect Password or Corrupted File!";
            }}
        }}

        // Allow pressing Enter to submit
        document.getElementById('passwordInput').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') unlockContent();
        }});
    </script>
</body>
</html>"""
    return html_template


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
        "• Self-decrypting HTML file मिलेगी\n"
        "• Keyboard & Copy Block protection\n\n"
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
            "4. Secured HTML file मिल जाएगी\n\n"
            "🛡️ Features:\n"
            "• AES-256-GCM Encryption\n"
            "• PBKDF2 Key Derivation\n"
            "• Copy & Inspect Block\n\n"
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
        encrypted_bytes = encrypt_data(bytes(file_bytes), password)
        html_wrapper = create_encrypted_html(encrypted_bytes, password)
        
        original_name = update.message.document.file_name or "file.html"
        base_name = original_name.rsplit(".", 1)[0]
        if base_name.endswith("_encrypted"):
            enc_name = base_name + ".html"
        else:
            enc_name = base_name + "_encrypted.html"
            
        file_size_kb = len(html_wrapper.encode('utf-8')) / 1024

        await update.message.reply_document(
            document=InputFile(io.BytesIO(html_wrapper.encode('utf-8')), filename=enc_name),
            caption=(
                f"✅ AES-256 GCM Eɴᴄʀʏᴘᴛɪᴏɴ Sᴜᴄᴄᴇssғᴜʟ!\n\n"
                f"📁 Fɪʟᴇ: <code>{enc_name}</code>\n"
                f"📦 Sɪᴢᴇ: {file_size_kb:.1f} KB\n\n"
                f"🔑 Yᴏᴜʀ Fɪʟᴇ Pᴀssᴡᴏʀᴅ: <code>{password}</code>\n\n"
                f"🛡️ Pʀᴏᴛᴇᴄᴛᴇᴅ ᴡɪᴛʜ:\n"
                f"• 🚫 AES-256-GCM Eɴᴄʀʏᴘᴛɪᴏɴ\n"
                f"• ⌨️ Kᴇʏʙᴏᴀʀᴅ & Cᴏᴘʏ Bʟᴏᴄᴋ\n"
                f"• 🌐 Eᴍᴏᴊɪ-Hᴇx Pᴀʏʟᴏᴀᴅ\n"
                f"• 🛡️ PBKDF2 Hᴀsʜ Dᴇʀɪᴠᴀᴛɪᴏɴ\n\n"
                f"👑 Yᴏᴜʀ cᴏᴅᴇ ɪs ɴᴏᴡ 100% pʀᴏᴛᴇᴄᴛᴇᴅ!"
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
    file_bytes = await file.download_as_bytearray()

    try:
        decrypted = decrypt_data(bytes(file_bytes), password)

        original_name = update.message.document.file_name or "decrypted"
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
            f"• Not a valid encrypted binary file\n\n"
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

    # Start the dummy HTTP server in background thread so Render web service passes health check
    threading.Thread(target=run_health_server, daemon=True).start()

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
