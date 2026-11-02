import os
import io
import logging
import threading
import random
import string
import requests
from urllib.parse import urlparse
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
BOT_TOKEN = "9143295973:AAGRCn-GHHJMMylM086i2V8c8wqgX9BAxNI"          # ← @BotFather se naya token daalo
REQUIRED_CHANNEL = "@UemRGWr-B2wzMmFl"
CHANNEL_LINK = "https://t.me/+UemRGWr-B2wzMmFl"

# ======================== LOGGING ========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======================== RENDER HEALTH CHECK ========================
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

# ======================== EMOJI MAPPING ========================
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

def decrypt_data(encrypted: bytes, password: str) -> bytes:
    if len(encrypted) < 28:
        raise ValueError("Invalid encrypted data")
    salt = encrypted[:16]
    nonce = encrypted[16:28]
    ciphertext = encrypted[28:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)

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

# ======================== MEMBERSHIP CHECK ========================
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logger.error(f"Membership check error: {e}")
    return False

# ======================== HANDLERS ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_joined = await check_membership(update, context)
    
    if not is_joined:
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel Now", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🔄 Verify Membership", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ **ACCESS DENIED!**\n\n"
            "Pehle channel join karo, phir **Verify Membership** dabao.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    text = (
        "╔══════════════════════════╗\n"
        "   🌟 **VIP ENCRYPTOR BOT** 🌟\n"
        "╚══════════════════════════╝\n\n"
        "Neeche se mode select karo:"
    )
    keyboard = [
        [
            InlineKeyboardButton("🔒 Encrypt HTML", callback_data="mode_encrypt"),
            InlineKeyboardButton("🔓 Decrypt HTML", callback_data="mode_decrypt")
        ],
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
            await query.message.edit_text("✅ Channel join ho gaya! Ab /start bhejo.")
        else:
            await query.message.edit_text("⚠️ Abhi bhi channel join nahi kiya hai.")
        return

    if query.data == "mode_encrypt":
        context.user_data.clear()
        context.user_data['mode'] = 'encrypt'
        await query.message.reply_text("🔒 **Encrypt Mode**\n\nAb koi bhi HTML file bhejo.")
    
    elif query.data == "mode_decrypt":
        context.user_data.clear()
        context.user_data['mode'] = 'decrypt'
        await query.message.reply_text(
            "🔓 **Decrypt Mode**\n\n"
            "1. Pehle encrypted HTML file bhejo\n"
            "2. Phir password bhejo"
        )
    
    elif query.data == "mode_url":
        context.user_data.clear()
        context.user_data['mode'] = 'url'
        await query.message.reply_text("🌐 **URL to HTML Mode**\n\nKoi bhi URL bhejo, main uska HTML de dunga.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await update.message.reply_text("⚠️ Pehle channel join karo!")
        return

    if not update.message.document:
        await update.message.reply_text("❌ Valid file bhejo.")
        return

    mode = context.user_data.get('mode')
    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    original_name = update.message.document.file_name or "file.html"

    await update.message.reply_text("⚡ Processing...")

    try:
        if mode == 'encrypt':
            password = generate_secure_password()
            encrypted_bytes = encrypt_data(bytes(file_bytes), password)
            emoji_payload = data_to_emojis(encrypted_bytes)
            html_wrapper = create_encrypted_html(emoji_payload)
            enc_name = original_name.rsplit(".", 1)[0] + "_emoji_secured.html"

            await update.message.reply_document(
                document=InputFile(io.BytesIO(html_wrapper.encode('utf-8')), filename=enc_name),
                caption=f"✅ **Encryption Successful!**\n\n🔑 **Password:** `{password}`",
                parse_mode="Markdown"
            )

        elif mode == 'decrypt':
            content_str = file_bytes.decode('utf-8', errors='ignore')

            if 'id="encryptedPayload"' not in content_str:
                await update.message.reply_text("❌ Yeh file encrypted format mein nahi hai.")
                return

            start_marker = 'id="encryptedPayload">'
            start_idx = content_str.find(start_marker)
            if start_idx == -1:
                await update.message.reply_text("❌ encryptedPayload nahi mila.")
                return

            start_idx += len(start_marker)
            end_idx = content_str.find('</div>', start_idx)
            if end_idx == -1:
                await update.message.reply_text("❌ Payload extract nahi hua.")
                return

            emoji_payload = content_str[start_idx:end_idx].strip()

            try:
                encrypted_bytes = emojis_to_data(emoji_payload)
            except Exception:
                await update.message.reply_text("❌ Emoji payload invalid hai.")
                return

            context.user_data['encrypted_bytes'] = encrypted_bytes
            context.user_data['original_name'] = original_name
            context.user_data['mode'] = 'await_password'

            await update.message.reply_text(
                "✅ Payload mil gaya!\n\n"
                "Ab **password** bhejo."
            )

        else:
            await update.message.reply_text("💡 Pehle mode select karo (/start).")

    except Exception as e:
        logger.exception("Document error")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        await update.message.reply_text("⚠️ Pehle channel join karo!")
        return

    text = update.message.text.strip()
    mode = context.user_data.get('mode')

    # ---------- Password step for Decrypt ----------
    if mode == 'await_password':
        encrypted_bytes = context.user_data.get('encrypted_bytes')
        original_name = context.user_data.get('original_name', 'file.html')

        if not encrypted_bytes:
            await update.message.reply_text("❌ Session expire. Phir se file bhejo.")
            context.user_data['mode'] = 'decrypt'
            return

        await update.message.reply_text("🔓 Decrypting...")

        try:
            plaintext = decrypt_data(encrypted_bytes, text)
            dec_name = original_name.rsplit(".", 1)[0] + "_decrypted.html"
            if not dec_name.lower().endswith('.html'):
                dec_name += '.html'

            await update.message.reply_document(
                document=InputFile(io.BytesIO(plaintext), filename=dec_name),
                caption="✅ **Successfully Decrypted!**"
            )
            context.user_data.clear()
            context.user_data['mode'] = 'decrypt'

        except Exception:
            await update.message.reply_text("❌ **Galat Password!**\nDobara password bhejo.")
        return

    # ---------- URL to HTML (Improved) ----------
    if mode == 'url' or text.startswith(("http://", "https://")):
        await update.message.reply_text("🌐 URL se HTML nikaal raha hoon...")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }

            response = requests.get(
                text,
                headers=headers,
                timeout=25,
                allow_redirects=True
            )
            response.raise_for_status()

            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = response.apparent_encoding

            html_content = response.text

            parsed = urlparse(text)
            domain = parsed.netloc.replace("www.", "").split(":")[0]
            file_name = f"{domain or 'website'}_converted.html"

            await update.message.reply_document(
                document=InputFile(io.BytesIO(html_content.encode('utf-8')), filename=file_name),
                caption=f"✅ **HTML mil gaya!**\n\n🔗 `{text}`\n📄 Size: {len(html_content)} characters",
                parse_mode="Markdown"
            )

        except requests.exceptions.RequestException as e:
            await update.message.reply_text(f"❌ URL fetch fail:\n`{str(e)}`", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        return

    await update.message.reply_text("💡 Pehle /start karke mode select karo.")

# ======================== MAIN ========================
def main():
    if not BOT_TOKEN or BOT_TOKEN == "9143295973:AAGRCn-GHHJMMylM086i2V8c8wqgX9BAxNI":
        print("❌ ERROR: Bot Token set karo!")
        return

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.Document.ALL & \~filters.COMMAND, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_text))

    print("🚀 Bot Started Successfully...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
