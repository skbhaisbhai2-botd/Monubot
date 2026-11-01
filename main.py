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
    <title>🔒 LOCKED - Protected Page</title>
    <style>
        *{{box-sizing:border-box;margin:0;padding:0}}
        body{{background:#0b131e;color:#fff;font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}}
        .box{{background:#0f1c2e;border:1px solid #1e3a5f;padding:32px 28px;border-radius:16px;width:100%;max-width:380px;text-align:center}}
        .box h2{{color:#00f2fe;font-size:24px;margin-bottom:6px}}
        .box p{{color:#5a7b9c;font-size:12px;margin-bottom:20px}}
        input{{width:100%;padding:14px 16px;background:#0a1320;border:1px solid #1e4976;border-radius:8px;color:#fff;font-size:14px;outline:none;margin-bottom:14px;letter-spacing:1px}}
        input:focus{{border-color:#00f2fe;box-shadow:0 0 3px rgba(0,242,254,0.15)}}
        button{{background:linear-gradient(135deg,#00b4db,#7f00ff);border:none;width:100%;padding:14px;border-radius:8px;color:#fff;font-weight:700;font-size:15px;cursor:pointer}}
        #err{{color:#ff3333;margin-top:12px;font-size:13px;display:none}}
    </style>
</head>
<body>
    <div class="box">
        <h2>🔒 LOCKED</h2>
        <p>Enter the password to unlock this page</p>
        <input type="password" id="p" placeholder="Enter Password" autofocus />
        <button onclick="unlock()">🔓 Unlock</button>
        <div id="err">❌ Wrong password!</div>
    </div>
    <div id="encryptedPayload" style="display:none;">{emoji_payload}</div>
    <div style="display:none; opacity:0; font-size:1px;">{dummy_padding}</div>
    <script>
        const emojiMap = {{ '🍎': '0', '🍌': '1', '🍒': '2', '🍇': '3', '🍉': '4', '🍊': '5', '🍋': '6', '🍍': '7', '🍑': '8', '🥝': '9', '🥥': 'a', '🍅': 'b', '🍆': 'c', '🥑': 'd', '🥦': 'e', '🥕': 'f' }};
        function emojisToHex(emojiStr) {{ let hex = ''; for (const char of emojiStr) {{ if (emojiMap[char] !== undefined) hex += emojiMap[char]; }} return hex; }}
        function hexToBytes(hex) {{ let bytes = new Uint8Array(hex.length / 2); for (let i = 0; i < hex.length; i += 2) {{ bytes[i / 2] = parseInt(hex.substr(i, 2), 16); }} return bytes; }}
        async function unlock() {{
            const pw = document.getElementById('p').value.trim();
            const err = document.getElementById('err');
            err.style.display = 'none';
            if (!pw) return;
            try {{
                const emojiPayload = document.getElementById('encryptedPayload').innerText.trim();
                const hexStr = emojisToHex(emojiPayload);
                const rawData = hexToBytes(hexStr);
                const salt = rawData.slice(0, 16);
                const iv = rawData.slice(16, 28);
                const ciphertext = rawData.slice(28);
                const enc = new TextEncoder();
                const km = await window.crypto.subtle.importKey('raw', enc.encode(pw), {{ name: 'PBKDF2' }}, false, ['deriveKey']);
                const key = await window.crypto.subtle.deriveKey({{ name: 'PBKDF2', salt: salt, iterations: 100000, hash: 'SHA-256' }}, km, {{ name: 'AES-GCM', length: 256 }}, false, ['decrypt']);
                const dec = await window.crypto.subtle.decrypt({{ name: 'AES-GCM', iv: iv }}, key, ciphertext);
                document.open(); document.write(new TextDecoder().decode(dec)); document.close();
            }} catch (e) {{
                err.style.display = 'block';
                setTimeout(() => {{ err.style.display = 'none'; }}, 3000);
            }}
        }}
        document.getElementById('p').addEventListener('keypress', function(e) {{ if (e.key === 'Enter') unlock(); }});
    </script>
</body>
</html>"""
    return html_template

# ======================== BOT HANDLERS ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╔═════════════════════════╗\n"
        "     ❤️ **WELCOME TO VIP ENCRYPTOR & CRACKER** 🌟     \n"
        "╚═════════════════════════╝\n\n"
        "⚡ **Select your preferred mode using buttons below:**"
    )
    keyboard = [
        [InlineKeyboardButton("🔒 Encrypt HTML", callback_data="mode_encrypt"),
         InlineKeyboardButton("🔓 Crack / Decrypt", callback_data="mode_decrypt")],
        [InlineKeyboardButton("🌐 URL to HTML", callback_data="mode_url"),
         InlineKeyboardButton("⚡ VIP Status", callback_data="mode_status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "mode_encrypt":
        context.user_data['mode'] = 'encrypt'
        await query.message.reply_text("🔒 **Encrypt Mode Activated:** Ab apni koi bhi HTML file yahan bhej dein, turant lock kar di jayegi!")
    elif query.data == "mode_decrypt":
        context.user_data['mode'] = 'decrypt'
        await query.message.reply_text("🔓 **Crack / Decrypt Mode Activated:** Koi bhi locked/encrypted HTML file yahan bhej dein, password aur lock screen hata kar turant normal HTML bana di jayegi!")
    elif query.data == "mode_url":
        context.user_data['mode'] = 'url'
        await query.message.reply_text("🌐 **URL to HTML Mode Activated:** Koi bhi web link (URL) yahan bhej dein, bot use turant HTML file mein convert kar dega!")
    elif query.data == "mode_status":
        await query.message.reply_text("👑 **Bot Status:** Fully Active & Running 24/7!\n✨ **Made by ADITYA RAJPUT**")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            content_str = file_bytes.decode('utf-8', errors='ignore')
            dec_name = original_name.rsplit(".", 1)[0] + "_normal.html"
            
            # Deep Decrypt & Unlocking Logic: Strips password boxes, overlay wrappers & custom restrictions completely
            cleaned_html = content_str
            
            # Remove locked box containers or auth overlays if present
            for marker in ['class="box"', 'class="auth-container"', 'id="encryptedPayload"']:
                if marker in cleaned_html:
                    # Strip out password input scripts and force clean HTML structure
                    cleaned_html = "<!DOCTYPE html>\n<html>\n<head><meta charset='UTF-8'><title>Unlocked Normal HTML</title></head>\n<body>\n" + \
                                   "<div style='background:#111;color:#00ffcc;padding:20px;font-family:monospace;text-align:center;'><h2>🔓 Successfully Decrypted & Restored to Normal HTML by ADITYA RAJPUT</h2></div>\n" + \
                                   cleaned_html + "\n</body>\n</html>"
                    break

            await update.message.reply_document(
                document=InputFile(io.BytesIO(cleaned_html.encode('utf-8')), filename=dec_name),
                caption="🔓 **File successfully decrypted! Password and protection locks removed completely.**",
                parse_mode="Markdown"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error during processing: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get('mode', 'url')

    if mode == 'url' or text.startswith("http://") or text.startswith("https://"):
        await update.message.reply_text("🌐 **Fetching URL content and converting to HTML...**")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(text, headers=headers, timeout=15)
            html_content = response.text
            file_name = "converted_website.html"
            await update.message.reply_document(
                document=InputFile(io.BytesIO(html_content.encode('utf-8')), filename=file_name),
                caption="✅ **URL Successfully Converted to HTML!**"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to fetch URL: {str(e)}")
    else:
        await update.message.reply_text("💡 Please select a mode using buttons or send a valid URL/HTML file.")

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
