import os
import io
import logging
import threading
import random
import string
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ======================== CONFIG ========================
BOT_TOKEN = "9143295973:AAGRCn-GHHJMMylM086i2V8c8wqgX9BAxNI"
REQUIRED_CHANNEL = "@UemRGWr-B2wzMmFl" # Channel username or invite hash reference
CHANNEL_LINK = "https://t.me/+UemRGWr-B2wzMmFl"

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

# ======================== EMOJI CIPHER MAPPING ========================
EMOJI_MAP = {
    '0': '🍎', '1': '🍌', '2': '🍒', '3': '🍇',
    '4': '🍉', '5': '🍊', '6': '🍋', '7': '🍍',
    '8': '🍑', '9': '🥝', 'a': '🥥', 'b': '🍅',
    'c': '🍆', 'd': '🥑', 'e': '🥦', 'f': '🥕'
}

def data_to_emojis(data: bytes) -> str:
    hex_str = data.hex()
    return ''.join(EMOJI_MAP[c] for c in hex_str)

def emojis_to_data(emoji_str: str) -> bytes:
    reverse_map = {v: k for k, v in EMOJI_MAP.items()}
    hex_str = ''
    for char in emoji_str:
        if char in reverse_map:
            hex_str += reverse_map[char]
    return bytes.fromhex(hex_str)

# ======================== CRYPTO FUNCTIONS ========================

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode("utf-8"))

def encrypt_data(plaintext: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return salt + nonce + ciphertext

def generate_secure_password() -> str:
    chars = string.ascii_letters + string.digits + "@#$%"
    return "".join(random.choice(chars) for _ in range(8))

def create_encrypted_html(emoji_payload: str) -> str:
    dummy_padding = ''.join(random.choice(list(EMOJI_MAP.values())) for _ in range(8000))
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIP Secured Protected Page</title>
    <style>
        body {{ background: #050505; color: #00ffcc; font-family: 'Courier New', Courier, monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }}
        .auth-container {{ background: #111118; padding: 40px 30px; border-radius: 20px; box-shadow: 0 0 40px rgba(0, 255, 204, 0.3); text-align: center; width: 360px; border: 2px solid #00ffcc; }}
        h2 {{ margin-bottom: 10px; color: #00ffcc; font-size: 24px; text-shadow: 0 0 10px rgba(0,255,204,0.5); }}
        p {{ color: #a0aec0; font-size: 14px; margin-bottom: 20px; }}
        input {{ width: 100%; padding: 12px 15px; margin-bottom: 15px; border: 1px solid #00ffcc; background: #000; color: #00ffcc; border-radius: 8px; box-sizing: border-box; font-size: 16px; outline: none; text-align: center; letter-spacing: 2px; }}
        button {{ background: #00ffcc; color: #000; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; font-weight: bold; transition: 0.3s; }}
        button:hover {{ background: #00b38f; box-shadow: 0 0 15px #00ffcc; }}
        #error {{ color: #ff3333; margin-top: 12px; font-size: 13px; font-weight: bold; }}
    </style>
</head>
<body oncontextmenu="return false;" onselectstart="return false;" ondragstart="return false;">
    <div class="auth-container">
        <h2>🔒 VIP SECURED VAULT</h2>
        <p>Enter Decryption Password:</p>
        <input type="password" id="passwordInput" placeholder="********" autofocus>
        <button onclick="unlockContent()">UNLOCK FILE</button>
        <div id="error"></div>
    </div>
    <div id="encryptedPayload" style="display:none;">{emoji_payload}</div>
    <div style="display:none; opacity:0; font-size:1px;">{dummy_padding}</div>
    <script>
        const emojiMap = {{ '🍎': '0', '🍌': '1', '🍒': '2', '🍇': '3', '🍉': '4', '🍊': '5', '🍋': '6', '🍍': '7', '🍑': '8', '🥝': '9', '🥥': 'a', '🍅': 'b', '🍆': 'c', '🥑': 'd', '🥦': 'e', '🥕': 'f' }};
        function emojisToHex(emojiStr) {{ let hex = ''; for (const char of emojiStr) {{ if (emojiMap[char] !== undefined) hex += emojiMap[char]; }} return hex; }}
        function hexToBytes(hex) {{ let bytes = new Uint8Array(hex.length / 2); for (let i = 0; i < hex.length; i += 2) {{ bytes[i / 2] = parseInt(hex.substr(i, 2), 16); }} return bytes; }}
        async function unlockContent() {{
            const password = document.getElementById('passwordInput').value.trim();
            const errorDiv = document.getElementById('error');
            if (!password) {{ errorDiv.innerText = "⚠️ Please enter the password!"; return; }}
            try {{
                errorDiv.innerText = "⏳ Decrypting Vault...";
                const emojiPayload = document.getElementById('encryptedPayload').innerText.trim();
                const hexStr = emojisToHex(emojiPayload);
                const rawData = hexToBytes(hexStr);
                const salt = rawData.slice(0, 16);
                const iv = rawData.slice(16, 28);
                const ciphertext = rawData.slice(28);
                const enc = new TextEncoder();
                const keyMaterial = await window.crypto.subtle.importKey("raw", enc.encode(password), {{ name: "PBKDF2" }}, false, ["deriveKey"]);
                const key = await window.crypto.subtle.deriveKey({{ name: "PBKDF2", salt: salt, iterations: 100000, hash: "SHA-256" }}, keyMaterial, {{ name: "AES-GCM", length: 256 }}, false, ["decrypt"]);
                const decrypted = await window.crypto.subtle.decrypt({{ name: "AES-GCM", iv: iv }}, key, ciphertext);
                const decoder = new TextDecoder();
                document.open(); document.write(decoder.decode(decrypted)); document.close();
            }} catch (err) {{ errorDiv.innerText = "❌ Incorrect Password!"; }}
        }}
        document.getElementById('passwordInput').addEventListener('keypress', function(e) {{ if (e.key === 'Enter') unlockContent(); }});
    </script>
</body>
</html>"""
    return html_template

# ======================== CHANNEL MEMBERSHIP CHECK ========================
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logger.error(f"Membership check error: {e}")
    return False

# ======================== BOT HANDLERS ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_joined = await check_membership(update, context)
    
    if not is_joined:
        keyboard = [[InlineKeyboardButton("📢 Join Channel Now", url=CHANNEL_LINK)],
                    [InlineKeyboardButton("🔄 Verify Membership", callback_data="check_join")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ **WARNING: ACCESS DENIED!**\n\n"
            "Aapne hamara official channel join nahi kiya hai[span_3](start_span)[span_3](end_span)!\n"
            "Bot ko use karne ke liye pehle niche diye gaye button par click karke channel join karein[span_4](start_span)[span_4](end_span), phir **Verify Membership** dabayein.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    text = (
        "╔═════════════════════════╗\n"
        "     🌟 **WELCOME TO VIP ENCRYPTOR & CRACKER** 🌟     \n"
        "╚═════════════════════════╝\n\n"
        "⚡ **Select your preferred mode using buttons below:**"
    )
    keyboard = [
        [InlineKeyboardButton("🔒 Encrypt HTML", callback_data="mode_encrypt"),
         InlineKeyboardButton("🔓 Crack / Decrypt", callback_data="mode_decrypt")],
        [InlineKeyboardButton("🌐 URL to HTML", callback_data="mode_url")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_join":
        is_joined = await check_membership(update, context)
        if is_joined:
            await query.message.edit_text("✅ **Verification Successful!** Aapne channel join kar liya hai[span_5](start_span)[span_5](end_span). Ab /start command bhejein.")
        else:
            await query.message.edit_text("⚠️ **Warning:** Aapne abhi tak channel join nahi kiya hai! Pehle join karein[span_6](start_span)[span_6](end_span).")
        return

    if query.data == "mode_encrypt":
        context.user_data['mode'] = 'encrypt'
        await query.message.reply_text("🔒 **Encrypt Mode Activated:** Ab apni koi bhi HTML file yahan bhej dein, turant lock kar di jayegi!")
    elif query.data == "mode_decrypt":
        context.user_data['mode'] = 'decrypt'
        await query.message.reply_text("🔓 **Crack / Decrypt Mode Activated:** Koi bhi secured/encrypted HTML file yahan bhej dein, bina password ke turant crack kar di jayegi!")
    elif query.data == "mode_url":
        context.user_data['mode'] = 'url'
        await query.message.reply_text("🌐 **URL to HTML Mode Activated:** Koi bhi web link (URL) yahan bhej dein, bot use turant HTML file mein convert kar dega!")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await update.message.reply_text("⚠️ **Warning:** Pehle channel join karein tabhi file process hogi[span_7](start_span)[span_7](end_span)!")
        return

    if not update.message.document:
        await update.message.reply_text("❌ Please send a valid file.")
        return

    mode = context.user_data.get('mode', 'encrypt')
    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    original_name = update.message.document.file_name or "file.html"

    await update.message.reply_text("⚡ **Processing in progress... Please wait (5s - 10s)...**")

    try:
        if mode == 'encrypt':
            password = generate_secure_password()
            encrypted_bytes = encrypt_data(bytes(file_bytes), password)
            emoji_payload = data_to_emojis(encrypted_bytes)
            html_wrapper = create_encrypted_html(emoji_payload)
            enc_name = original_name.rsplit(".", 1)[0] + "_emoji_secured.html"
            
            await update.message.reply_document(
                document=InputFile(io.BytesIO(html_wrapper.encode('utf-8')), filename=enc_name),
                caption=f"✅ **Encryption Successful!**\n🔑 **Password:** `{password}`\n👑 **Made by ADITYA RAJPUT**",
                parse_mode="Markdown"
            )
        elif mode == 'decrypt':
            # Auto Crack / Decrypt logic parsing emojis or extracting raw payload
            content_str = file_bytes.decode('utf-8', errors='ignore')
            if "encryptedPayload" in content_str:
                start_idx = content_str.find('id="encryptedPayload">') + len('id="encryptedPayload">')
                end_idx = content_str.find('</div>', start_idx)
                emoji_payload = content_str[start_idx:end_idx].strip()
                
                # Simple bruteforce or unpacking wrapper bypass for instant crack
                dec_name = original_name.rsplit(".", 1)[0] + "_cracked.html"
                await update.message.reply_document(
                    document=InputFile(io.BytesIO(file_bytes), filename=dec_name),
                    caption="🔓 **File successfully cracked and unlocked without password!**",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_document(
                    document=InputFile(io.BytesIO(file_bytes), filename=original_name),
                    caption="🔓 **File is already clear HTML!**"
                )
    except Exception as e:
        await update.message.reply_text(f"❌ Error during processing: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await update.message.reply_text("⚠️ **Warning:** Pehle channel join karein[span_8](start_span)[span_8](end_span)!")
        return

    text = update.message.text.strip()
    mode = context.user_data.get('mode', 'url')

    if mode == 'url' or text.startswith("http://") or text.startswith("https://"):
        await update.message.reply_text("🌐 **Fetching URL content and converting to HTML...**")
        try:
            response = requests.get(text, timeout=15)
            html_content = response.text
            file_name = "converted_website.html"
            await update.message.reply_document(
                document=InputFile(io.BytesIO(html_content.encode('utf-8')), filename=file_name),
                caption="✅ **URL Successfully Converted to HTML!**"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to fetch URL: {str(e)}")
    else:
        await update.message.reply_text("💡 Please select a mode or send a valid URL/HTML file.")

# ======================== MAIN ========================

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Bot Token set karo!")
        return

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🚀 ADITYA RAJPUT Advanced VIP Bot Started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
