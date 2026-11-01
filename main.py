import os
import io
import logging
import threading
import random
import string
from http.server import HTTPServer, BaseHTTPRequestHandler
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
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
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secured HTML File</title>
    <style>
        body {
            background: #0f172a;
            color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        .auth-container {
            background: #1e293b;
            padding: 35px 30px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
            text-align: center;
            width: 340px;
            border: 1px solid #334155;
        }
        h2 { margin-bottom: 10px; color: #38bdf8; font-size: 22px; }
        p { color: #94a3b8; font-size: 14px; margin-bottom: 20px; }
        input {
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
        }
        input:focus { border-color: #38bdf8; }
        button {
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
        }
        button:hover { background: #1d4ed8; }
        #error { color: #ef4444; margin-top: 12px; font-size: 13px; font-weight: 500; }
    </style>
</head>
<body oncontextmenu="return false;" onselectstart="return false;" ondragstart="return false;">
    <div class="auth-container">
        <h2>🔒 Secured Page</h2>
        <p>Enter password to unlock:</p>
        <input type="password" id="passwordInput" placeholder="Enter Password" autofocus>
        <button onclick="unlockContent()">Unlock File</button>
        <div id="error"></div>
    </div>

    <script>
        const emojiMap = {
            '🍎': '0', '🍌': '1', '🍒': '2', '🍇': '3',
            '🍉': '4', '🍊': '5', '🍋': '6', '🍍': '7',
            '🍑': '8', '🥝': '9', '🥥': 'a', '🍅': 'b',
            '🍆': 'c', '🥑': 'd', '🥦': 'e', '🥕': 'f'
        };

        function emojisToHex(emojiStr) {
            let hex = '';
            for (let char of emojiStr) {
                if (emojiMap[char] !== undefined) {
                    hex += emojiMap[char];
                }
            }
            return hex;
        }

        function hexToBytes(hex) {
            let bytes = new Uint8Array(hex.length / 2);
            for (let i = 0; i < hex.length; i += 2) {
                bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
            }
            return bytes;
        }

        document.addEventListener('keydown', function(e) {
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C' || e.key === 'J')) || 
                (e.ctrlKey && e.key === 'u')) {
                e.preventDefault();
                return false;
            }
        });

        async function unlockContent() {
            const password = document.getElementById('passwordInput').value;
            const errorDiv = document.getElementById('error');
            
            if (!password) {
                errorDiv.innerText = "⚠️ Please enter the password!";
                return;
            }

            try {
                errorDiv.innerText = "⏳ Decrypting...";
                const emojiPayload = "REPLACE_EMOJI_PAYLOAD";
                const hexStr = emojisToHex(emojiPayload);
                const rawData = hexToBytes(hexStr);

                const salt = rawData.slice(0, 16);
                const iv = rawData.slice(16, 28);
                const ciphertext = rawData.slice(28);

                const enc = new TextEncoder();
                const keyMaterial = await window.crypto.subtle.importKey(
                    "raw", enc.encode(password), { name: "PBKDF2" }, false, ["deriveKey"]
                );
                
                const key = await window.crypto.subtle.deriveKey(
                    { name: "PBKDF2", salt: salt, iterations: 100000, hash: "SHA-256" },
                    keyMaterial,
                    { name: "AES-GCM", length: 256 },
                    false,
                    ["decrypt"]
                );

                const decrypted = await window.crypto.subtle.decrypt(
                    { name: "AES-GCM", iv: iv }, key, ciphertext
                );

                const decoder = new TextDecoder();
                const htmlContent = decoder.decode(decrypted);

                document.open();
                document.write(htmlContent);
                document.close();
            } catch (err) {
                errorDiv.innerText = "❌ Incorrect Password!";
            }
        }

        document.getElementById('passwordInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') unlockContent();
        });
    </script>
</body>
</html>"""
    return html_template.replace("REPLACE_EMOJI_PAYLOAD", emoji_payload)


# ======================== BOT HANDLERS ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 <b>ADITYA RAJPUT EMOJI ENCRYPTOR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "• Koi bhi <b>HTML file</b> seedha yahan bhej do!\n"
        "• Bot turant 2 second mein auto-password ke sath encrypt kar dega.\n"
        "• Poora code **Emojis** mein locked milega! 🍎🍌🍒"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("❌ Please send an HTML file.")
        return

    file = await update.message.document.get_file()
    file_bytes = await file.download_as_bytearray()
    original_name = update.message.document.file_name or "file.html"

    try:
        password = generate_secure_password()
        encrypted_bytes = encrypt_data(bytes(file_bytes), password)
        emoji_payload = data_to_emojis(encrypted_bytes)
        html_wrapper = create_encrypted_html(emoji_payload)
        
        enc_name = original_name.rsplit(".", 1)[0] + "_emoji_secured.html"
        file_size_kb = len(html_wrapper.encode('utf-8')) / 1024

        await update.message.reply_document(
            document=InputFile(io.BytesIO(html_wrapper.encode('utf-8')), filename=enc_name),
            caption=(
                f"✅ <b>Instant Encryption Successful!</b>\n\n"
                f"📁 File: <code>{enc_name}</code>\n"
                f"📦 Size: {file_size_kb:.1f} KB\n\n"
                f"🔑 <b>Auto Password:</b> <code>{password}</code>\n\n"
                f"🛡️ <b>Protected with:</b>\n"
                f"• AES-256-GCM + PBKDF2\n"
                f"• 🍎 Emoji Cipher Payload\n"
                f"• Keyboard & Copy Block\n\n"
                f"<b>Made by ADITYA RAJPUT</b>"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# ======================== MAIN ========================

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Bot Token set karo!")
        return

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_document))

    print("🚀 ADITYA RAJPUT Emoji Encryptor Bot Started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
