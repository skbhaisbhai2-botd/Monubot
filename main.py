# FULL OSINT BOT CODE WITH COMPLETE MEDIA GALLERY SYSTEM
# UPDATED: New APIs for /num, /adhr, /tgid
# UPDATED: All results in blockquote format
# UPDATED: Full info display for all APIs

import sqlite3
import requests
import json
import time
import re
import logging
import os
import sys
import random
import string
import threading
from datetime import datetime, timedelta
from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile, MessageEntity
from threading import Lock, Thread
from concurrent.futures import ThreadPoolExecutor
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib
from collections import OrderedDict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ===== PREMIUM EMOJI IDs =====
PREMIUM_EMOJI_IDS = [
"4956420859771225351",
"4958626617535497157",
"4958734459869332468",
"4956282853882069908",
"4956247175588742152",
"5296491800423340716",
"4956739572114392015",
"4956606007221421405",
"4958617898751886363",
"4956290155326473271",
"4958714479681471536",
"4956461073550017373",
"4956719506027185156",
"5116414868357907335",
"4958587679361991667",
"4956560549287560231",
"4956539525422646612",
"6127546175240280564",
"6127558265573218459",
"5084613633418199991",
"5098265504796115765",
"5116296632203216188",
"6147565374289220368",
"6147464060305676048",
"6235459831302460476",
"6235355429237430006",
"6129434968713076807",
"6129828611055689014",
"6129700535130922338"
]

def get_random_premium_emoji_id():
    return random.choice(PREMIUM_EMOJI_IDS)

# ============================================================
# PREMIUM EMOJI MAP — NUMBER INFO SPECIFIC
# ============================================================
NUM_EMOJIS = {
    "header_divider": "5467641505525016018",   # ➿
    "phone_title":    "6172503852785342178",   # 📞
    "status_ok":      "6129812419028982717",   # ✅
    "query":          "5379999674193172777",   # 🔭
    "records":        "5197269100878907942",   # ✍️
    "record_badge":   "5249231689695115145",   # 📰
    "number":         "6026092115631543342",   # 📲
    "name":           "5425124408786197150",   # 👤
    "father":         "5258513401784573443",   # 👥
    "alt_num":        "5453965363286925977",   # 📞
    "circle":         "5895476993314524652",   # 🔎
    "address":        "4958485609464202497",   # 🏡
    "id_card":        "5985796637971191405",   # 💳
    "email":          "5303416490295304868",   # 📧
    "speed":          "6203911118964924015",   # 🚀
    "credits":        "5326049357332513437",   # 🧱
    "bot_icon":       "5355051922862653659",   # 🤖
    "star":           "6118385795976930086",   # 🌟
}
# ============================================================
# PREMIUM EMOJI MAP — AADHAR INFO SPECIFIC
# ============================================================
ADHR_EMOJIS = {
    "header_divider": "5467641505525016018",   # ➿
    "adhr_title":     "6030753228889526497",   # 🪪
    "status_ok":      "6071022434234930063",   # ✅
    "query":          "5379999674193172777",   # 🔭
    "records":        "5197269100878907942",   # ✍️
    "record_badge":   "5249231689695115145",   # 📰
    "mobile":         "6026092115631543342",   # 📲
    "name":           "5425124408786197150",   # 👤
    "circle":         "5375365992891312468",   # 🛜
    "address":        "4958485609464202497",   # 🏡
    "id_card":        "5985796637971191405",   # 💳
    "speed":          "6203911118964924015",   # 🚀
    "credits":        "5931368295545443065",   # 📊
    "bot_icon":       "5355051922862653659",   # 🤖
    "star":           "6118385795976930086",   # 🌟
    "father":         "5258513401784573443",   # 👥
    "email":          "5303416490295304868",   # 📧
}

def build_adhr_divider() -> str:
    d = te(ADHR_EMOJIS["header_divider"], "➿")
    return (d * 8) + "\n"

# ============================================================
# PREMIUM EMOJI MAP — VEHICLE / RC SPECIFIC
# ============================================================
VECH_EMOJIS = {
    "header_divider": "5467641505525016018",   # ➿
    "veh_title":      "5323272789824654613",   # 🪪
    "rc_number":      "6093653759378858331",   # 🚗
    "source":         "5798417071796653494",   # 💎
    "status_ok":      "6129812419028982717",   # ✅
    "vehicle":        "5312322066328853156",   # 🚗
    "make":           "6077707920198338212",   # 🏭
    "mfg_year":       "6021757076290675447",   # 🗓️
    "fuel":           "5359588280205605798",   # ⚡️
    "vclass":         "6226775738142432221",   # 👿
    "cc":             "4904936030232117798",   # ⚙️
    "seating":        "5260732577026696524",   # 🐸
    "colour":         "5926764846518376076",   # 📋
    "body":           "6233262422954613958",   # 🏎
    "owner":          "5832263552982851814",   # 👨‍🦰
    "mobile":         "6104960836311195547",   # 📲
    "address":        "4958485609464202497",   # 🏡
    "registration":   "5226929552319594190",   # 0️⃣
    "reg_date":       "5472279086657199080",   # 🗓️
    "rto":            "6303001048185309018",   # 🗺
    "rto_code":       "5422449357125350081",   # 🔢
    "financer":       "5264733042710181045",   # 🏢
    "commercial":     "5796205953913196373",   # 💎
    "insurance":      "5188688567970308198",   # 🏎
    "ins_status":     "6300604035527346062",   # 🛡
    "technical":      "5341715473882955310",   # ⚙️
    "chassis":        "5258023599419171861",   # 🔧
    "engine":         "4967657001023701985",   # ⚙️
    "norms":          "4904936030232117798",   # ⚙️
    "speed":          "6203911118964924015",   # 🚀
    "credits":        "5326049357332513437",   # 🧱
    "bot_icon":       "5355051922862653659",   # 🤖
    "star":           "6118385795976930086",   # 🌟
    "query":          "5379999674193172777",   # 🔭
    "records":        "5197269100878907942",   # ✍️
    "record_badge":   "5249231689695115145",   # 📰
}

def build_vech_divider() -> str:
    d = te(VECH_EMOJIS["header_divider"], "➿")
    return (d * 12) + "\n"


def te(emoji_id: str, fallback: str = "⭐") -> str:
    """Shorthand: build a <tg-emoji> tag."""
    return f"<tg-emoji emoji-id='{emoji_id}'>{fallback}</tg-emoji>"

def build_num_divider() -> str:
    d = te(NUM_EMOJIS["header_divider"], "➿")
    return (d * 8) + "\n"


# ===== PREMIUM EMOJI REPLACEMENT SYSTEM =====
EMOJI_TO_PREMIUM = {
    "⚠": "4956420859771225351",
    "⚡": "4958626617535497157",
    "✅": "4958734459869332468",
    "✏": "4956282853882069908",
    "✨": "4956247175588742152",
    "❌": "5296491800423340716",
    "❓": "4956739572114392015",
    "❤": "4956606007221421405",
    "➕": "4958617898751886363",
    "➖": "4956290155326473271",
    "➡": "4958714479681471536",
    "🌍": "4956461073550017373",
    "🌐": "4956719506027185156",
    "🌟": "5116414868357907335",
    "🎂": "4958587679361991667",
    "🎉": "4956560549287560231",
    "🎥": "4956539525422646612",
    "🎨": "6127546175240280564",
    "🎫": "6127558265573218459",
    "🎬": "5084613633418199991",
    "🎮": "5098265504796115765",
    "🏆": "5116414868357907335",
    "🏙": "5116296632203216188",
    "🏠": "6147565374289220368",
    "🏦": "6147464060305676048",
    "🐙": "6235459831302460476",
    "👋": "6235355429237430006",
    "👑": "6129434968713076807",
    "👤": "6129828611055689014",
    "👥": "6129700535130922338",
    "👦": "4956420859771225351",
    "👧": "4958626617535497157",
    "👨": "4958734459869332468",
    "👩": "4956282853882069908",
    "💡": "4956247175588742152",
    "💬": "5296491800423340716",
    "💰": "4956739572114392015",
    "💳": "4956606007221421405",
    "📄": "4958617898751886363",
    "📅": "4956290155326473271",
    "📈": "4958714479681471536",
    "📊": "4956461073550017373",
    "📋": "4956719506027185156",
    "📌": "5116414868357907335",
    "📍": "4958587679361991667",
    "📚": "4956560549287560231",
    "📛": "4956539525422646612",
    "📝": "6127546175240280564",
    "📞": "6127558265573218459",
    "📢": "5084613633418199991",
    "📥": "5098265504796115765",
    "📧": "5116414868357907335",
    "📨": "5116296632203216188",
    "📮": "6147565374289220368",
    "📱": "6147464060305676048",
    "📸": "6235459831302460476",
    "📺": "6235355429237430006",
    "🔄": "6129434968713076807",
    "🔍": "6129828611055689014",
    "🔐": "6129700535130922338",
    "🔑": "4956420859771225351",
    "🔒": "4958626617535497157",
    "🔓": "4958734459869332468",
    "🔔": "4956282853882069908",
    "🔗": "4956247175588742152",
    "🔘": "5296491800423340716",
    "🔙": "4956739572114392015",
    "🔢": "4956606007221421405",
    "🔥": "4958617898751886363",
    "🔧": "4956290155326473271",
    "🕐": "4958714479681471536",
    "🖼": "4956461073550017373",
    "🗑": "4956719506027185156",
    "🗺": "5116414868357907335",
    "🚗": "4958587679361991667",
    "🚫": "4956560549287560231",
    "🛑": "4956539525422646612",
    "🟢": "6127546175240280564",
    "🧪": "6127558265573218459",
    "⭐": "5116414868357907335",
    "🆔": "6129828611055689014",
    "🆕": "6129700535130922338",
    "🎰": "4956560549287560231",
}

def replace_with_premium_emojis(text):
    """Replace all free emojis in text with random premium Telegram emoji tags.
    Existing <tg-emoji> tags are preserved untouched."""
    if not text or not isinstance(text, str):
        return text

    import re

    # Step 1: Protect existing <tg-emoji> tags
    tg_emoji_pattern = re.compile(r"<tg-emoji emoji-id='\d+'>[^<]*</tg-emoji>")
    placeholders = []
    def protect(match):
        placeholders.append(match.group(0))
        return f"[[P_{len(placeholders)-1}]]"
    text = tg_emoji_pattern.sub(protect, text)

    # Step 2: Replace free emojis with premium tags
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"   # Emoticons 😀-🙏
        "\U0001F300-\U0001F5FF"   # Misc Symbols & Pictographs 🌀-🗿
        "\U0001F680-\U0001F6FF"   # Transport & Map 🚀-🛿
        "\U0001F1E0-\U0001F1FF"   # Flags 🇠-🇿
        "\U00002702-\U000027B0"   # Dingbats ✂-➰
        "\U0001F900-\U0001F9FF"   # Supplemental Symbols & Pictographs
        "\U0001FA00-\U0001FA6F"   # Chess Symbols
        "\U0001FA70-\U0001FAFF"   # Symbols & Pictographs Extended-A
        "\U00002600-\U000026FF"   # Misc Symbols ☀-⛿
        "\U00002B00-\U00002BFF"   # Misc Symbols & Arrows
        "\U00002300-\U000023FF"   # Misc Technical
        "\U0001F7E0-\U0001F7FF"   # Geometric Shapes Extended
        "\U0000200D"                # ZWJ
        "\U000024C2-\U000024FF"   # Enclosed Alphanumerics Ⓜ-Ⓩ
        "\U0001F000-\U0001F02F"   # Mahjong Tiles
        "\U0001F0A0-\U0001F0FF"   # Playing Cards
        "\U0001F200-\U0001F2FF"   # Enclosed Ideographic Supplement
        "]+", flags=re.UNICODE
    )

    def replace_emoji(match):
        random_id = get_random_premium_emoji_id()
        return f"<tg-emoji emoji-id='{random_id}'>⭐</tg-emoji>"

    text = emoji_pattern.sub(replace_emoji, text)

    # Step 3: Restore protected tags
    for i, original in enumerate(placeholders):
        text = text.replace(f"[[P_{i}]]", original)

    return text

def truncate_text(text, max_length=10000):
    """Truncate text safely without breaking HTML tags"""
    if not text:
        return text
    if len(text) <= max_length:
        return text

    truncate_msg = "\n\n<blockquote>... (truncated - download JSON for full data)</blockquote>"
    available = max_length - len(truncate_msg)

    # Find last complete </blockquote> before max_length
    search_text = text[:available]
    last_close = search_text.rfind('</blockquote>')

    if last_close > 0:
        cut_point = last_close + len('</blockquote>')
        return text[:cut_point] + truncate_msg
    else:
        return text[:available] + truncate_msg


def send_with_premium(
    chat_id,
    text,
    reply_markup=None,
    parse_mode="HTML",
    reply_to_message_id=None,
    disable_notification=False,
    protect_content=False
):
    text = replace_with_premium_emojis(text)

    if "<tg-emoji" not in text:
        premium_emoji_id = get_random_premium_emoji_id()
        text = f"{text} <tg-emoji emoji-id='{premium_emoji_id}'>⭐</tg-emoji>"
    return bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        reply_to_message_id=reply_to_message_id,
        disable_notification=disable_notification,
        protect_content=protect_content
    )

def edit_with_premium(chat_id, message_id, text, reply_markup=None, parse_mode='HTML'):
    text = replace_with_premium_emojis(text)

    if "<tg-emoji" not in text:
        premium_emoji_id = get_random_premium_emoji_id()
        text = f"{text} <tg-emoji emoji-id='{premium_emoji_id}'>⭐</tg-emoji>"

    try:
        return bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        logger.error(f"Premium emoji edit failed: {e}")
        try:
            return bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=reply_markup
            )
        except:
            return None

def send_searching_animation(chat_id):
    try:
        return send_with_premium(chat_id, "🔍 Searching...")
    except Exception as e:
        return send_with_premium(chat_id, "🔍 Searching...")

def stop_searching_animation(chat_id, message_id, final_text, reply_markup=None):
    try:
        return edit_with_premium(chat_id, message_id, final_text, reply_markup=reply_markup)
    except:
        return send_with_premium(chat_id, final_text, reply_markup=reply_markup)

# ============================================================
# BUTTON FUNCTIONS WITH STYLES AND **kwargs SUPPORT
# ============================================================

def create_primary_button(text, callback_data=None, url=None, **kwargs):
    """Primary style button with kwargs support"""
    return InlineKeyboardButton(text=text, callback_data=callback_data, url=url, **kwargs)

def create_success_button(text, callback_data=None, url=None, **kwargs):
    """Success style button with kwargs support"""
    return InlineKeyboardButton(text=text, callback_data=callback_data, url=url, **kwargs)

def create_danger_button(text, callback_data=None, url=None, **kwargs):
    """Danger style button with kwargs support"""
    return InlineKeyboardButton(text=text, callback_data=callback_data, url=url, **kwargs)

def create_default_button(text, callback_data=None, url=None, **kwargs):
    """Default style button with kwargs support"""
    return InlineKeyboardButton(text=text, callback_data=callback_data, url=url, **kwargs)

class SimpleCache:
    def __init__(self, maxsize=100, ttl=300):
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}

    def get(self, key):
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key, value):
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.maxsize:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
            del self.timestamps[oldest]
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def clear(self):
        self.cache.clear()
        self.timestamps.clear()

BOT_TOKEN = "8725919398:AAFYnEeXu5evZDrhU5Q2d_w582xpCITyAuE"
ADMIN_ID = 8611613363
OWNER_USERNAME = "RAJPUT BHAI"

API_BASE_URL = "https://ft-osint-api.duckdns.org"
API_KEY = "sahil-new"

FORCE_JOIN_ENABLED = True

JSON_FILES = {}
NUM_PAGINATION = {}   # user_id -> {"pages": [(txt, markup), ...], "json_file": path}
LAST_PROCESSED_UPDATE_ID = 0
API_CACHE = SimpleCache(maxsize=100, ttl=300)
EXECUTOR = ThreadPoolExecutor(max_workers=10)

POSTS_CACHE = {}

API_ENDPOINTS = {
    "tgid": "/api?key={key}&type=tg&term={query}",
    "num": "/api/number?key={key}&num={query}",
    "name": "/api/name?key={key}&name={query}",
    "pan": "/api/pan?key={key}&pan={query}",
    "vech": "/api/vehicle?key={key}&vehicle={query}",
    "vechrc": "/api/rc?key={key}&owner={query}",
    "ip": "/api/ip?key={key}&ip={query}",
    "pin": "/api/pincode?key={key}&pin={query}",
    "git": "/api/git?key={key}&username={query}",
    "bgmi": "/api/bgmi?key={key}&uid={query}",
    "ff": "/api/ff?key={key}&uid={query}",
    "adhr": "/api/aadhar?key={key}&num={query}",
    "upi": "/api/upi?key={key}&upi={query}",
    "ifsc": "/api/ifsc?key={key}&ifsc={query}",
    "family": "https://ayaanmods.site/family.php?key=annonymousfamily&term={query}",
}

NEW_USER_CREDITS = 10
REFERRAL_BONUS_REFERRER = 5
REFERRAL_BONUS_NEW = 10
COMMAND_COST = 1
AUTO_DELETE_TIME = 120

DB_FILE = 'osintbBBBRO_bot.db'
db_lock = Lock()
bot = TeleBot(BOT_TOKEN, num_threads=20)

BOT_LOCKED = False
BOT_START_TIME = datetime.now()
BLOCKED_USERS = set()

API_STATUS = {
    "tgid": {"working": True, "message": None},
    "num": {"working": True, "message": None},
    "num2": {"working": True, "message": None},
    "name": {"working": True, "message": None},
    "pan": {"working": True, "message": None},
    "vech": {"working": True, "message": None},
    "vechrc": {"working": True, "message": None},
    "ip": {"working": True, "message": None},
    "pin": {"working": True, "message": None},
    "git": {"working": True, "message": None},
    "bgmi": {"working": True, "message": None},
    "ff": {"working": True, "message": None},
    "adhr": {"working": True, "message": None},
    "upi": {"working": True, "message": None},
    "ifsc": {"working": True, "message": None},
    "insta": {"working": True, "message": None},
    "ai": {"working": True, "message": None},
    "family": {"working": True, "message": None},
}

def check_api_status(command):
    status = API_STATUS.get(command, {"working": True, "message": None})
    return status["working"], status.get("message")

def set_api_status(command, working, message=None):
    if command in API_STATUS:
        API_STATUS[command]["working"] = working
        API_STATUS[command]["message"] = message
        return True
    return False

MEDIA_MODE = "both"

def init_media_tables():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("""
                    CREATE TABLE IF NOT EXISTS media_videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id TEXT NOT NULL,
                        description TEXT,
                        added_by INTEGER,
                        added_date TEXT,
                        is_active INTEGER DEFAULT 1
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS media_photos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id TEXT NOT NULL,
                        description TEXT,
                        added_by INTEGER,
                        added_date TEXT,
                        is_active INTEGER DEFAULT 1
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS media_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_key TEXT UNIQUE,
                        setting_value TEXT,
                        updated_by INTEGER,
                        updated_date TEXT
                    )
                """)
                try:
                    c.execute("ALTER TABLE media_videos ADD COLUMN description TEXT")
                    print("Added description column to media_videos")
                except:
                    pass
                try:
                    c.execute("ALTER TABLE media_photos ADD COLUMN description TEXT")
                    print("Added description column to media_photos")
                except:
                    pass
                c.execute("UPDATE media_videos SET description = 'Video' WHERE description IS NULL")
                c.execute("UPDATE media_photos SET description = 'Photo' WHERE description IS NULL")
                conn.commit()
                print("Media gallery tables ready")
        except Exception as e:
            print(f"Media tables error: {e}")
        finally:
            if conn:
                conn.close()

def load_media_mode():
    global MEDIA_MODE
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT setting_value FROM media_settings WHERE setting_key = 'media_mode'")
                result = c.fetchone()
                if result:
                    MEDIA_MODE = result[0]
                else:
                    MEDIA_MODE = "both"
                    c.execute("INSERT INTO media_settings (setting_key, setting_value, updated_date) VALUES (?, ?, ?)",
                             ("media_mode", "both", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                print(f"Media mode loaded: {MEDIA_MODE}")
        except Exception as e:
            print(f"Load media mode error: {e}")
        finally:
            if conn:
                conn.close()

def set_media_mode(mode, admin_id):
    global MEDIA_MODE
    if mode not in ["video", "photo", "both"]:
        return False, "Invalid mode! Use: video, photo, or both"
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO media_settings (setting_key, setting_value, updated_by, updated_date) VALUES (?, ?, ?, ?)",
                         ("media_mode", mode, admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                MEDIA_MODE = mode
                return True, f"Media mode set to: {mode.upper()}"
        except Exception as e:
            return False, f"Error: {e}"
        finally:
            if conn:
                conn.close()
    return False, "Error"

def add_video(file_id, description, admin_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("INSERT INTO media_videos (file_id, description, added_by, added_date, is_active) VALUES (?, ?, ?, ?, 1)",
                         (file_id, description, admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                return True, "Video added!"
        except Exception as e:
            print(f"Add video error: {e}")
            return False, f"Error: {str(e)}"
        finally:
            if conn:
                conn.close()
    return False, "Error"

def add_photo(file_id, description, admin_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT id FROM media_photos WHERE file_id = ?", (file_id,))
                if c.fetchone():
                    return False, "Photo already exists! (Duplicate)"
                c.execute("INSERT INTO media_photos (file_id, description, added_by, added_date, is_active) VALUES (?, ?, ?, ?, 1)",
                         (file_id, description, admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                return True, "Photo added successfully!"
        except Exception as e:
            return False, f"Error: {e}"
        finally:
            if conn:
                conn.close()
    return False, "Error"

def delete_video(video_id, admin_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("DELETE FROM media_videos WHERE id = ?", (int(video_id),))
                affected = c.rowcount
                conn.commit()
                if affected > 0:
                    return True, f"Deleted {affected} video(s)!"
                return False, "Video not found!"
        except Exception as e:
            return False, f"Error: {e}"
        finally:
            if conn:
                conn.close()
    return False, "Error"

def delete_photo(photo_id, admin_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("DELETE FROM media_photos WHERE id = ?", (int(photo_id),))
                affected = c.rowcount
                conn.commit()
                if affected > 0:
                    return True, "Deleted photo successfully!"
                return False, "Photo not found!"
        except Exception as e:
            return False, f"Error: {e}"
        finally:
            if conn:
                conn.close()
    return False, "Error"

def get_random_video():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT file_id, description FROM media_videos WHERE is_active = 1 AND description IS NOT NULL ORDER BY RANDOM() LIMIT 1")
                result = c.fetchone()
                if result:
                    return {"file_id": result[0], "description": result[1] or "Video", "type": "video"}
                return None
        except Exception as e:
            print(f"Get random video error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    return None

def get_random_photo():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT file_id, description FROM media_photos WHERE is_active = 1 ORDER BY RANDOM() LIMIT 1")
                result = c.fetchone()
                if result:
                    return {"file_id": result[0], "description": result[1] or "Photo", "type": "photo"}
                return None
        except Exception as e:
            print(f"Get random photo error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    return None

def get_all_videos():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT id, file_id, description, added_by, added_date FROM media_videos WHERE is_active = 1 ORDER BY id DESC")
                return c.fetchall()
        except Exception as e:
            print(f"Get all videos error: {e}")
            return []
        finally:
            if conn:
                conn.close()
    return []

def get_all_photos():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT id, file_id, description, added_by, added_date FROM media_photos WHERE is_active = 1 ORDER BY id DESC")
                return c.fetchall()
        except Exception as e:
            print(f"Get all photos error: {e}")
            return []
        finally:
            if conn:
                conn.close()
    return []

def get_video_count():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM media_videos WHERE is_active = 1")
                return c.fetchone()[0] or 0
        except:
            return 0
        finally:
            if conn:
                conn.close()
    return 0

def get_photo_count():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM media_photos WHERE is_active = 1")
                return c.fetchone()[0] or 0
        except:
            return 0
        finally:
            if conn:
                conn.close()
    return 0

def send_random_media(chat_id, reply_to_message_id=None):
    try:
        if MEDIA_MODE == "video":
            video = get_random_video()
            if video:
                vcap = replace_with_premium_emojis(f"🎬 {video['description']}")
                bot.send_video(chat_id, video["file_id"], caption=vcap, parse_mode='HTML', reply_to_message_id=reply_to_message_id)
                return True
        elif MEDIA_MODE == "photo":
            photo = get_random_photo()
            if photo:
                pcap = replace_with_premium_emojis(f"🖼️ {photo['description']}")
                bot.send_photo(chat_id, photo["file_id"], caption=pcap, parse_mode='HTML', reply_to_message_id=reply_to_message_id)
                return True
        elif MEDIA_MODE == "both":
            video_count = get_video_count()
            photo_count = get_photo_count()
            if video_count > 0 and photo_count > 0:
                if random.choice([True, False]):
                    video = get_random_video()
                    if video:
                        vcap = replace_with_premium_emojis(f"🎬 {video['description']}")
                        bot.send_video(chat_id, video["file_id"], caption=vcap, parse_mode='HTML', reply_to_message_id=reply_to_message_id)
                        return True
                else:
                    photo = get_random_photo()
                    if photo:
                        pcap = replace_with_premium_emojis(f"🖼️ {photo['description']}")
                        bot.send_photo(chat_id, photo["file_id"], caption=pcap, parse_mode='HTML', reply_to_message_id=reply_to_message_id)
                        return True
            elif video_count > 0:
                video = get_random_video()
                if video:
                    vcap = replace_with_premium_emojis(f"🎬 {video['description']}")
                    bot.send_video(chat_id, video["file_id"], caption=vcap, parse_mode='HTML', reply_to_message_id=reply_to_message_id)
                    return True
            elif photo_count > 0:
                photo = get_random_photo()
                if photo:
                    pcap = replace_with_premium_emojis(f"🖼️ {photo['description']}")
                    bot.send_photo(chat_id, photo["file_id"], caption=pcap, parse_mode='HTML', reply_to_message_id=reply_to_message_id)
                    return True
    except Exception as e:
        print(f"Send random media error: {e}")
    return False


def init_database():
    with db_lock:
        conn = None
        try:
            conn = sqlite3.connect(DB_FILE, timeout=10)
            cursor = conn.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA synchronous=NORMAL')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    credits INTEGER DEFAULT 10,
                    is_admin INTEGER DEFAULT 0,
                    referred_by INTEGER,
                    referral_count INTEGER DEFAULT 0,
                    join_date TEXT,
                    last_active TEXT,
                    total_commands INTEGER DEFAULT 0,
                    joined_channel1 INTEGER DEFAULT 0,
                    joined_channel2 INTEGER DEFAULT 0,
                    joined_channel3 INTEGER DEFAULT 0,
                    is_blocked INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    date TEXT,
                    credits_given INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS redeem_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    credits INTEGER,
                    max_uses INTEGER,
                    used_count INTEGER DEFAULT 0,
                    expiry_date TEXT,
                    created_by INTEGER,
                    created_date TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS code_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    used_date TEXT,
                    UNIQUE(code, user_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS force_join_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    username TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    added_by INTEGER,
                    added_date TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_name TEXT UNIQUE,
                    api_endpoint TEXT,
                    updated_by INTEGER,
                    updated_date TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dynamic_apis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command_name TEXT UNIQUE,
                    api_endpoint TEXT NOT NULL,
                    api_key TEXT,
                    param_name TEXT DEFAULT 'query',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_by INTEGER,
                    created_date TEXT,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_chats (
                    chat_id INTEGER PRIMARY KEY,
                    chat_title TEXT,
                    chat_type TEXT,
                    added_date TEXT,
                    last_active TEXT,
                    member_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            """)
            conn.commit()
            print("SQLite Database Ready")
        except Exception as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

def load_blocked_users():
    global BLOCKED_USERS
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT user_id FROM users WHERE is_blocked = 1")
                blocked = c.fetchall()
                BLOCKED_USERS = {row[0] for row in blocked}
                print(f"Loaded {len(BLOCKED_USERS)} blocked users")
        except Exception as e:
            print(f"Error loading blocked users: {e}")
        finally:
            if conn:
                conn.close()

def block_user_in_db(user_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                BLOCKED_USERS.add(user_id)
                return True
        except:
            return False
        finally:
            if conn:
                conn.close()
    return False

def unblock_user_in_db(user_id):
    global BLOCKED_USERS
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
                conn.commit()
                BLOCKED_USERS.discard(user_id)
                return True
        except:
            return False
        finally:
            if conn:
                conn.close()
    return False

def check_user_access(user_id):
    if user_id == ADMIN_ID:
        return True
    if user_id in BLOCKED_USERS:
        return False
    if BOT_LOCKED:
        return False
    return True

def get_access_error_message(user_id):
    if user_id in BLOCKED_USERS:
        return f"""
BANNED

YOU HAVE BEEN BANNED

Contact Admin: {OWNER_USERNAME}
"""
    elif BOT_LOCKED:
        return """
BOT LOCKED

BOT IS LOCKED BY ADMIN

Please wait for admin to unlock the bot
"""
    return None
def get_db():

    try:
        conn = sqlite3.connect(DB_FILE, timeout=10, check_same_thread=False, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        return conn
    except Exception:
        return None

def get_user(user_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return None
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return c.fetchone()
        except Exception:
            return None
        finally:
            if conn:
                conn.close()

def create_user(user_id, username, first_name, referred_by=None):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return False
            c = conn.cursor()
            join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            if c.fetchone():
                return False
            credits = NEW_USER_CREDITS
            is_admin = 1 if user_id == ADMIN_ID else 0
            if referred_by and referred_by != user_id:
                c.execute("SELECT * FROM users WHERE user_id = ?", (referred_by,))
                referrer = c.fetchone()
                if referrer:
                    c.execute("UPDATE users SET credits = credits + ?, referral_count = referral_count + 1 WHERE user_id = ?", 
                             (REFERRAL_BONUS_REFERRER, referred_by))
                    c.execute("INSERT INTO referrals (referrer_id, referred_id, date, credits_given) VALUES (?, ?, ?, ?)",
                             (referred_by, user_id, join_date, REFERRAL_BONUS_REFERRER))
                    credits += REFERRAL_BONUS_NEW
            c.execute("""INSERT INTO users (user_id, username, first_name, credits, join_date, 
                        referred_by, referral_count, last_active, is_admin, joined_channel1, joined_channel2, joined_channel3, is_blocked)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (user_id, username or "N/A", first_name or "User", credits, join_date, 
                       referred_by if referred_by and referred_by != user_id else None, 
                       0, join_date, is_admin, 0, 0, 0, 0))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            if conn:
                conn.close()

def get_credits(user_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return 0
            c = conn.cursor()
            c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            return result[0] if result else 0
        except Exception:
            return 0
        finally:
            if conn:
                conn.close()

def deduct_credit(user_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return True
            c = conn.cursor()
            c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            if not result:
                return True
            if result[0] <= 0:
                return False
            c.execute("UPDATE users SET credits = credits - 1, total_commands = total_commands + 1, last_active = ? WHERE user_id = ?", 
                     (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
            conn.commit()
            return True
        except Exception:
            return True
        finally:
            if conn:
                conn.close()

def add_credits(user_id, amount):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return False
            c = conn.cursor()
            c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            if conn:
                conn.close()

def is_admin(user_id):
    if user_id == ADMIN_ID:
        return True
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
                result = c.fetchone()
                if result and result[0] == 1:
                    return True
        except:
            pass
        finally:
            if conn:
                conn.close()
    return False

def check_code_used_by_user(code, user_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT id FROM code_usage WHERE code = ? AND user_id = ?", (code.upper(), user_id))
                result = c.fetchone()
                if result:
                    return True
                return False
        except Exception as e:
            print(f"Check code usage error: {e}")
            return False
        finally:
            if conn:
                conn.close()
    return False

def record_code_usage(code, user_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("INSERT INTO code_usage (code, user_id, used_date) VALUES (?, ?, ?)",
                         (code.upper(), user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return True
        except Exception as e:
            print(f"Record code usage error: {e}")
            return False
        finally:
            if conn:
                conn.close()
    return False

def redeem_credits(user_id, code):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return False, "Database error!"
            c = conn.cursor()
            c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not c.fetchone():
                return False, "User not found! Please /start first."
            c.execute("SELECT id FROM code_usage WHERE code = ? AND user_id = ?", (code, user_id))
            if c.fetchone():
                return False, "You have already used this redeem code! Each code can be used only once per user."
            c.execute("""SELECT id, credits, max_uses, used_count, expiry_date, is_active 
                        FROM redeem_codes WHERE code = ?""", (code,))
            result = c.fetchone()
            if not result:
                return False, "Invalid code! Code does not exist."
            code_id, credits, max_uses, used_count, expiry_date, is_active = result
            if not is_active:
                return False, "Code is inactive! Contact admin."
            if expiry_date:
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
                if expiry < datetime.now():
                    return False, "Code expired!"
            if used_count >= max_uses:
                return False, "Code max usage reached! This code has been fully used."
            c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (credits, user_id))
            c.execute("INSERT INTO code_usage (code, user_id, used_date) VALUES (?, ?, ?)",
                     (code, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            c.execute("UPDATE redeem_codes SET used_count = used_count + 1 WHERE id = ?", (code_id,))
            conn.commit()
            c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
            new_balance = c.fetchone()[0]
            return True, f"Successfully redeemed {credits} credits! New balance: {new_balance}"
        except sqlite3.IntegrityError as e:
            return False, f"Database integrity error: {str(e)}"
        except Exception as e:
            print(f"Redeem error: {e}")
            return False, f"Error: {str(e)}"
        finally:
            if conn:
                conn.close()

def create_redeem_code(code, credits, max_uses, expiry_date, admin_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return False, "Database error"
            c = conn.cursor()
            c.execute("""INSERT INTO redeem_codes 
                        (code, credits, max_uses, expiry_date, created_by, created_date, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (code.upper(), credits, max_uses, expiry_date, 
                      admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
            conn.commit()
            return True, f"Code created: {code}"
        except sqlite3.IntegrityError:
            return False, "Code already exists!"
        except Exception as e:
            return False, str(e)
        finally:
            if conn:
                conn.close()

def delete_redeem_code(code, admin_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return False, "Database error!"
            c = conn.cursor()
            c.execute("SELECT id, code, credits, max_uses, used_count FROM redeem_codes WHERE code = ? AND is_active = 1", (code.upper(),))
            result = c.fetchone()
            if not result:
                return False, "Code not found or already inactive!"
            code_id, code_str, credits, max_uses, used_count = result
            c.execute("UPDATE redeem_codes SET is_active = 0 WHERE id = ?", (code_id,))
            conn.commit()
            return True, f"Code `{code_str}` deleted successfully!\n\nStats:\nCredits: {credits}\nMax Uses: {max_uses}\nUsed: {used_count} times"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            if conn:
                conn.close()

def get_bot_stats():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if not conn:
                return {}
            c = conn.cursor()
            stats = {}
            c.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = c.fetchone()[0] or 0
            c.execute("SELECT SUM(credits) FROM users")
            stats['total_credits'] = c.fetchone()[0] or 0
            c.execute("SELECT SUM(total_commands) FROM users")
            stats['total_commands'] = c.fetchone()[0] or 0
            today = datetime.now().strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM users WHERE join_date LIKE ?", (f"{today}%",))
            stats['today_users'] = c.fetchone()[0] or 0
            c.execute("SELECT SUM(referral_count) FROM users")
            stats['total_referrals'] = c.fetchone()[0] or 0
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("SELECT COUNT(*) FROM users WHERE last_active > ?", (yesterday,))
            stats['active_users'] = c.fetchone()[0] or 0
            return stats
        except Exception:
            return {}
        finally:
            if conn:
                conn.close()

init_database()
init_media_tables()
load_media_mode()
load_blocked_users()
print("Database initialized successfully")


PROMOTION_CHANNELS = []
def load_channels_from_db():
    global PROMOTION_CHANNELS
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute('SELECT url, username, enabled FROM force_join_channels WHERE enabled = 1')
                channels = c.fetchall()
                if channels:
                    PROMOTION_CHANNELS = [{"url": row[0], "username": row[1], "enabled": bool(row[2])} for row in channels]
                else:
                    default_channels = [
                        ("https://t.me/bynxgc", "bynxgc", True),
                        ("https://t.me/Osintxarmy", "Osintxarmy", True),
                        ("https://t.me/osint_by_nx", "OSINT_BY_NX", True)
                    ]
                    for url, username, enabled in default_channels:
                        c.execute("""INSERT INTO force_join_channels (url, username, enabled, added_by, added_date) 
                                    VALUES (?, ?, ?, ?, ?)""", 
                                 (url, username, enabled, ADMIN_ID, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    PROMOTION_CHANNELS = [{"url": url, "username": username, "enabled": enabled} for url, username, enabled in default_channels]
                print(f"Loaded {len(PROMOTION_CHANNELS)} force join channels")
        except Exception as e:
            print(f"Error loading channels: {e}")
        finally:
            if conn:
                conn.close()

def add_force_join_channel(url, username, admin_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("""INSERT INTO force_join_channels (url, username, enabled, added_by, added_date) 
                            VALUES (?, ?, ?, ?, ?)""",
                         (url, username, 1, admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                PROMOTION_CHANNELS.append({"url": url, "username": username, "enabled": True})
                return True, "Channel added successfully!"
        except sqlite3.IntegrityError:
            return False, "Channel already exists!"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            if conn:
                conn.close()
    return False, "Database error!"

def remove_force_join_channel(url_or_username, admin_id):
    global PROMOTION_CHANNELS
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT id, url, username FROM force_join_channels WHERE url = ? OR username = ?", 
                         (url_or_username, url_or_username.replace('@', '')))
                channel = c.fetchone()
                if not channel:
                    return False, "Channel not found!"
                channel_id, url, username = channel
                c.execute("DELETE FROM force_join_channels WHERE id = ?", (channel_id,))
                conn.commit()
                PROMOTION_CHANNELS = [ch for ch in PROMOTION_CHANNELS if ch['url'] != url and ch['username'] != username]
                return True, f"Channel removed: {url}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            if conn:
                conn.close()
    return False, "Database error!"

def list_force_join_channels():
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT id, url, username, enabled, added_by, added_date FROM force_join_channels ORDER BY id")
                return c.fetchall()
        except Exception as e:
            print(f"Error listing channels: {e}")
        finally:
            if conn:
                conn.close()
    return []

def check_subscription(user_id):
    if not FORCE_JOIN_ENABLED:
        return True
    if user_id == ADMIN_ID:
        return True
    if not PROMOTION_CHANNELS:
        load_channels_from_db()
    if not PROMOTION_CHANNELS:
        return True
    for channel in PROMOTION_CHANNELS:
        if not channel.get('enabled', True):
            continue
        try:
            member = bot.get_chat_member(f"@{channel['username']}", user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False
    return True

def get_missing_channels(user_id):
    missing = []
    if not FORCE_JOIN_ENABLED:
        return missing
    if user_id == ADMIN_ID:
        return missing
    if not PROMOTION_CHANNELS:
        load_channels_from_db()
    for channel in PROMOTION_CHANNELS:
        if not channel.get('enabled', True):
            continue
        try:
            member = bot.get_chat_member(f"@{channel['username']}", user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                missing.append(channel['url'])
        except Exception:
            missing.append(channel['url'])
    return missing

def force_join_message(chat_id, user_id):
    missing = get_missing_channels(user_id)
    if not missing:
        return None
    channels_text = "\n".join([f"{i+1}. {ch}" for i, ch in enumerate(missing)])
    msg = f"""
FORCE JOIN REQUIRED

 YOU MUST JOIN ALL CHANNELS TO USE THIS BOT!

CHANNELS TO JOIN:
{channels_text}

 After joining all channels, click the button below to verify!
"""
    markup = InlineKeyboardMarkup(row_width=1)
    for channel in missing:
        markup.add(create_primary_button("Join Channel", url=channel, icon_custom_emoji_id="5219899949281453881"))
    markup.add(create_success_button("I've Joined All", callback_data="check_join"))
    try:
        return send_with_premium(chat_id, msg, reply_markup=markup)
    except Exception as e:
        print(f"Force join message error: {e}")
        return None

def enforce_force_join(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id == ADMIN_ID:
        return True
    if not check_subscription(user_id):
        force_join_message(chat_id, user_id)
        return False
    return True

def schedule_deletion(message_id, chat_id):
    def delete():
        time.sleep(AUTO_DELETE_TIME)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    thread = threading.Thread(target=delete)
    thread.daemon = True
    thread.start()

def extract_referral(text):
    if text and 'ref_' in text:
        try:
            return int(text.split('ref_')[1])
        except:
            return None
    return None

def send_result_with_json(chat_id, result_text, json_file, message_id=None, edit=True):
    final_text = result_text
    file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
    JSON_FILES[file_id] = json_file

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(create_primary_button("Download JSON", callback_data=f"dljson_{file_id}"))
    markup.add(create_default_button("Back", callback_data="back_to_result"))

    try:
        if message_id and edit:
            try:
                sent = edit_with_premium(chat_id, message_id, final_text, reply_markup=markup)
                schedule_deletion(sent.message_id, chat_id)
                return sent
            except:
                pass
        sent = send_with_premium(chat_id, final_text, reply_markup=markup)
        schedule_deletion(sent.message_id, chat_id)
        return sent
    except Exception as e:
        print(f"Error sending result: {e}")
        return None

def send_result(chat_id, result_text, wait_message=None, edit=True):
    final_text = replace_with_premium_emojis(result_text)
    if "<tg-emoji" not in final_text:
        premium_emoji_id = get_random_premium_emoji_id()
        final_text = final_text + f" <tg-emoji emoji-id='{premium_emoji_id}'>⭐</tg-emoji>"
    try:
        if wait_message and edit:
            try:
                sent = edit_with_premium(chat_id, wait_message.message_id, final_text)
                if sent:
                    schedule_deletion(sent.message_id, chat_id)
                    return sent
            except Exception as e:
                print(f"Edit failed, sending new message: {e}")
                try:
                    bot.delete_message(chat_id, wait_message.message_id)
                except:
                    pass
        sent = send_with_premium(chat_id, final_text)
        schedule_deletion(sent.message_id, chat_id)
        return sent
    except Exception as e:
        print(f"Error sending result: {e}")
        return None

load_channels_from_db()

def validate_username(u):
    if not u: return False
    u = u.strip().replace('@', '')
    return bool(re.match(r'^[a-zA-Z0-9_]{5,32}$', u))

def validate_phone(p):
    if not p: return False
    p = re.sub(r'[^\d+]', '', p)
    return bool(re.match(r'^\+?[0-9]{10,15}$', p))

def validate_vehicle(v):
    if not v: return False
    v = v.strip().upper().replace(' ', '')
    return bool(re.match(r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{1,4}$', v))

def validate_upi(upi):
    if not upi: return False
    upi = upi.strip().lower()
    return bool(re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$', upi))

def validate_ifsc(ifsc):
    if not ifsc: return False
    ifsc = ifsc.strip().upper()
    return bool(re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc))

def validate_aadhar(a):
    if not a: return False
    a = re.sub(r'[^\d]', '', a)
    return bool(re.match(r'^\d{12}$', a))

def validate_pan(pan):
    if not pan: return False
    pan = pan.strip().upper()
    return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan))

def validate_ip(ip):
    if not ip: return False
    return bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip))

def validate_pincode(pin):
    if not pin: return False
    pin = re.sub(r'[^\d]', '', pin)
    return bool(re.match(r'^\d{6}$', pin))

def validate_channel_url(url):
    if not url: return False
    patterns = [r'^https?://t\.me/[a-zA-Z0-9_]+$', r'^https?://telegram\.me/[a-zA-Z0-9_]+$', r'^@[a-zA-Z0-9_]+$']
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False


def is_group_chat(message):
    return message.chat.type in ['group', 'supergroup', 'channel']

def extract_username_from_url(url):
    url = url.strip()
    if url.startswith('@'):
        return url[1:]
    elif 't.me/' in url:
        return url.split('t.me/')[-1]
    elif 'telegram.me/' in url:
        return url.split('telegram.me/')[-1]
    return url

def get_emoji_for_key(key):
    key_lower = key.lower()
    if 'name' in key_lower: return '👤'
    elif 'phone' in key_lower or 'number' in key_lower or 'mobile' in key_lower: return '📞'
    elif 'email' in key_lower: return '📧'
    elif 'address' in key_lower: return '🏠'
    elif 'city' in key_lower or 'state' in key_lower: return '📍'
    elif 'bank' in key_lower: return '🏦'
    elif 'ifsc' in key_lower: return '🔢'
    elif 'vehicle' in key_lower or 'car' in key_lower: return '🚗'
    elif 'owner' in key_lower: return '👨'
    elif 'aadhar' in key_lower: return '🆔'
    elif 'pan' in key_lower: return '📄'
    elif 'upi' in key_lower: return '💳'
    elif 'instagram' in key_lower or 'insta' in key_lower: return '📸'
    elif 'followers' in key_lower: return '👑'
    elif 'ip' in key_lower: return '🌐'
    elif 'pincode' in key_lower: return '📮'
    elif 'git' in key_lower: return '🐙'
    elif 'bgmi' in key_lower: return '🎮'
    elif 'ff' in key_lower: return '🔥'
    elif 'prompt' in key_lower or 'image' in key_lower: return '🎨'
    elif 'generated' in key_lower: return '🖼️'
    elif 'father' in key_lower: return '👨'
    elif 'circle' in key_lower: return '🌍'
    elif 'alt' in key_lower or 'alternate' in key_lower: return '📱'
    elif 'id' in key_lower: return '🆔'
    elif 'truecaller' in key_lower: return '👤'
    elif 'country' in key_lower: return '🌍'
    elif 'code' in key_lower: return '🔢'
    elif 'total' in key_lower: return '📊'
    elif 'result' in key_lower: return '📋'
    else: return '•'

print("Validation functions loaded")

def get_api_endpoint(command_name):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT api_endpoint FROM api_config WHERE command_name = ?", (command_name,))
                result = c.fetchone()
                if result:
                    return result[0]
        except:
            pass
        finally:
            if conn:
                conn.close()
    return None

def set_api_endpoint(command_name, endpoint, admin_id):
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("""INSERT OR REPLACE INTO api_config (command_name, api_endpoint, updated_by, updated_date) 
                            VALUES (?, ?, ?, ?)""",
                         (command_name, endpoint, admin_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                return True, f"API endpoint updated for /{command_name}"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            if conn:
                conn.close()
    return False, "Database error!"

def list_all_apis():
    apis = []
    for cmd, endpoint in API_ENDPOINTS.items():
        apis.append({'command': cmd, 'endpoint': endpoint, 'is_custom': False})
    with db_lock:
        conn = None
        try:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("SELECT command_name, api_endpoint FROM api_config")
                custom = c.fetchall()
                for cmd, endpoint in custom:
                    apis.append({'command': cmd, 'endpoint': endpoint, 'is_custom': True})
        except:
            pass
        finally:
            if conn:
                conn.close()
    return apis

def clean_text(text):
    if isinstance(text, str):
        text = text.replace("@DEVELOPERSTAKEBOT", "").strip()
        text = text.replace("@ and @TATANIUM_ANSH", "@ftgamer2")
        text = text.replace("@InvalidAyush", "").strip()
        text = text.replace("InvalidAyush", "⏤͟͟͞͞𝗦ᴀ𝗛ɪ𝗟").strip()
        text = text.replace("developer", "⏤͟͟͞͞𝗦ᴀ𝗛ɪ𝗟").strip()
        text = text.replace("Developer", "⏤͟͟͞͞𝗦ᴀ𝗛ɪ𝗟").strip()
        text = text.replace("@InvalidAyush ❤️🔥⚡", "⏤͟͟͞͞𝗦ᴀ𝗛ɪ𝗟 ❤️🔥⚡").strip()
        text = text.replace("❤️🔥⚡", "").strip()
        words = text.split()
        cleaned_words = []
        for word in words:
            if word.startswith('@') and word not in ['@ftgamer2', '@BMW_AURA0', '@sahilxalone']:
                continue
            cleaned_words.append(word)
        return ' '.join(cleaned_words)
    return text

def clean_dict(data):
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if key.lower() in ['channel', 'developer', 'by', 'tag', 'key_expiry', 'response_time_ms', 'cached', 'cached_at', 'owner', 'credit', 'message']:
                continue
            if isinstance(value, str):
                cleaned[key] = clean_text(value)
            elif isinstance(value, dict):
                cleaned[key] = clean_dict(value)
            elif isinstance(value, list):
                cleaned[key] = [clean_dict(item) if isinstance(item, dict) else (clean_text(item) if isinstance(item, str) else item) for item in value]
            else:
                cleaned[key] = value
        cleaned['developer'] = '⏤͟͟͞͞𝗦ᴀ𝗛ɪ𝗟'
        cleaned['contact'] = 'http://t.me/sahilxalone'
        return cleaned
    elif isinstance(data, list):
        return [clean_dict(item) if isinstance(item, dict) else (clean_text(item) if isinstance(item, str) else item) for item in data]
    elif isinstance(data, str):
        return clean_text(data)
    return data

def is_empty_response(data):
    if not data:
        return True
    if isinstance(data, dict):
        if data.get('status') == 'error' or data.get('error'):
            return True
        all_empty = True
        for key, value in data.items():
            if key in ['status', 'by', 'channel']:
                continue
            if value and str(value).strip() and str(value).lower() not in ['none', 'null', '']:
                all_empty = False
                break
        return all_empty
    return False

def make_api_request(url, timeout=10):
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cached = API_CACHE.get(cache_key)
    if cached:
        return cached
    try:
        response = session.get(url, timeout=timeout, verify=False)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and data.get('status') != 'error':
                    API_CACHE.set(cache_key, data)
                return data
            except:
                return {"status": "error", "message": "Invalid JSON"}
        return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def call_phone_api(phone):
    phone = re.sub(r'[^\d+]', '', phone).lstrip('+')
    try:
        url = f"https://sahilcc.dpdns.org/api/num?number={phone}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if isinstance(data, dict) and data.get('results'):
                cleaned_data = {
                    "status": "success",
                    "number": data.get('number', phone),
                    "total": data.get('total', 0),
                    "records": []
                }
                for idx, result in enumerate(data.get('results', []), 1):
                    record = {
                        "record_no": idx,
                        "mobile": result.get('mobile', 'N/A'),
                        "name": result.get('name', 'N/A'),
                        "address": result.get('address', 'N/A').replace('!', ', '),
                        "circle": result.get('circle', 'N/A'),
                        "alternate": result.get('alt', 'N/A'),
                        "father_name": result.get('fname', 'N/A'),
                        "id": result.get('id', 'N/A'),
                        "email": result.get('email', 'Not Available'),
                        "truecaller_name": result.get('truecaller_name', 'N/A')
                    }
                    cleaned_data['records'].append(record)
                return clean_dict(cleaned_data)
            elif data.get('success') == True and data.get('total', 0) == 0:
                return {"status": "error", "message": "NO DATA FOUND"}
            return {"status": "error", "message": "NO DATA FOUND"}
        return {"status": "error", "message": "NO DATA FOUND"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def call_tg_api(query):
    query = str(query).strip()
    query = query.replace('@', '').replace('t.me/', '').replace('telegram.me/', '')
    is_user_id = query.isdigit()

    def parse_api_response(data, original_query):
        if not isinstance(data, dict) or data.get('success') != True:
            return None
        msg = data.get('msg', '')
        if 'not found' in msg.lower() or 'no data' in msg.lower():
            return None
        phone = data.get('number') or None
        country = data.get('country') or None
        country_code = data.get('country_code') or None
        tgid = None
        for field in ['tg_id', 'user_id', 'id', 'userid', 'userId', 'UID']:
            if field in data and data[field] is not None:
                tgid = data[field]
                break
        username = None
        for field in ['username', 'user_name', 'uname', 'tg_username']:
            if field in data and data[field] is not None:
                username = data[field]
                break
        if not phone:
            return None
        return {
            'status': 'success',
            'query': original_query,
            'found': True,
            'tgid': str(tgid) if tgid is not None else 'N/A',
            'username': str(username) if username is not None else 'N/A',
            'phone': str(phone),
            'country': str(country) if country else 'N/A',
            'country_code': str(country_code) if country_code else 'N/A',
            'msg': msg or 'Details fetched',
            'provided_by': '⏤͟͟͞͞RAJPUT BHAI',
            'telegram': 'RAJPUT BHAI',
        }

    try:
        if is_user_id:
            url1 = f"https://rootx-osint.in/?type=tg_num&key=sahil_X&query={query}"
        else:
            url1 = f"https://rootx-osint.in/?type=tg_num&key=sahil_X&query=@{query}"
        data1 = make_api_request(url1, timeout=15)
        result = parse_api_response(data1, query)
        if result:
            return result
    except Exception as e1:
        print(f"[TGID] Attempt 1 error: {e1}")

    try:
        if is_user_id:
            url2 = f"http://broad-dust-ad2f.mohammadumar7221.workers.dev/api/tg?key=ftgamer&info={query}"
        else:
            url2 = f"http://broad-dust-ad2f.mohammadumar7221.workers.dev/api/tg?key=ftgamer&info=@{query}"
        data2 = make_api_request(url2, timeout=15)
        result = parse_api_response(data2, query)
        if result:
            return result
    except Exception as e2:
        print(f"[TGID] Attempt 2 error: {e2}")

    try:
        if is_user_id:
            url3 = f"https://api.igfollows.site/TG/index.php?type=user&key=OGGYxKRISH&term={query}"
        else:
            url3 = f"https://api.igfollows.site/TG/index.php?type=user&key=OGGYxKRISH&term=@{query}"
        data3 = make_api_request(url3, timeout=15)
        if isinstance(data3, dict) and data3.get('success') == True:
            msg = data3.get('msg', '')
            if 'not found' not in msg.lower() and 'no data' not in msg.lower():
                phone = data3.get('number') or data3.get('n') or None
                country = data3.get('country') or data3.get('c') or None
                country_code = data3.get('country_code') or data3.get('cc') or None
                tgid = data3.get('tg_id') or data3.get('id') or None
                if phone:
                    return {
                        'status': 'success',
                        'query': query,
                        'found': True,
                        'tgid': str(tgid) if tgid else 'N/A',
                        'username': 'N/A',
                        'phone': str(phone),
                        'country': str(country) if country else 'N/A',
                        'country_code': str(country_code) if country_code else 'N/A',
                        'msg': msg or 'Details fetched',
                        'provided_by': '⏤͟͟͞͞𝗦ᴀ𝗛ɪ𝗟',
                        'telegram': '@sahilxalone',
                    }
    except Exception as e3:
        print(f"[TGID] Attempt 3 error: {e3}")

    if is_user_id:
        try:
            chat = bot.get_chat(int(query))
            if chat and chat.username:
                username = chat.username
                url4 = f"https://rootx-osint.in/?type=tg_num&key=sahil_X&query=@{username}"
                data4 = make_api_request(url4, timeout=15)
                result = parse_api_response(data4, query)
                if result:
                    result['note'] = f'Resolved from User ID to @{username}'
                    return result
        except Exception as e4:
            print(f"[TGID] Attempt 4 error: {e4}")

    return {"status": "error", "message": "NO DATA FOUND"}

def call_aadhar_api(aadhar_number):
    """Fetch from felix-true.onrender.com and normalise into standard record dicts."""
    aadhar = re.sub(r'[^\d]', '', aadhar_number)
    try:
        url = f"https://felix-true.onrender.com/api?key=sahil987&adhar={aadhar}"
        data = make_api_request(url, timeout=35)

        if not isinstance(data, dict):
            return {"status": "error", "message": "NO DATA FOUND"}

        # felix API: top-level status bool
        if not (data.get('status') is True or data.get('success') is True):
            return {"status": "error", "message": data.get('message', 'NO DATA FOUND')}

        inner = data.get('data', {})
        raw_records = inner.get('records', [])
        total = inner.get('total_records', len(raw_records))

        if not raw_records:
            return {"status": "error", "message": "NO DATA FOUND"}

        # key_details for credits display
        key_details = data.get('key_details', {})

        records = []
        for r in raw_records:
            records.append({
                "record_no":   r.get('record', len(records) + 1),
                "mobile":      str(r.get('mobile', 'N/A')).strip(),
                "name":        r.get('name', 'N/A'),
                "father_name": r.get('father', 'N/A'),
                "address":     r.get('address', 'N/A'),
                "circle":      r.get('circle', 'N/A'),
                "aadhar":      str(inner.get('adhar', aadhar)),
                "email":       r.get('email', 'N/A') if r.get('email') and r.get('email') != 'default@unspecify.com' else 'N/A',
            })

        return clean_dict({
            "status":      "success",
            "aadhar":      aadhar,
            "total":       total,
            "records":     records,
            "key_details": key_details,
        })

    except Exception as e:
        return {"status": "error", "message": str(e)}

def build_api_url(endpoint_template, query):
    url = endpoint_template
    url = url.replace("{key}", API_KEY)
    url = url.replace("{query}", str(query))
    url = url.replace("phone", str(query))
    url = url.replace("num", str(query))
    url = url.replace("name", str(query))
    url = url.replace("pan", str(query))
    url = url.replace("vehicle", str(query))
    url = url.replace("owner", str(query))
    url = url.replace("ip", str(query))
    url = url.replace("pin", str(query))
    url = url.replace("username", str(query))
    url = url.replace("uid", str(query))
    url = url.replace("upi", str(query))
    url = url.replace("ifsc", str(query))
    return url

def call_name_api(name):
    try:
        custom_endpoint = get_api_endpoint('name')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, name)
        else:
            url = f"{API_BASE_URL}/api/name?key={API_KEY}&name={name}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_pan_api(pan):
    pan = pan.strip().upper()
    try:
        custom_endpoint = get_api_endpoint('pan')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, pan)
        else:
            url = f"{API_BASE_URL}/api/pan?key={API_KEY}&pan={pan}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_vehicle_api(vehicle):
    vehicle = vehicle.strip().upper().replace(' ', '')
    try:
        # NEW API: sahilcc.dpdns.org
        url = f"http://sahilcc.dpdns.org/api/veh?vehicle={vehicle}"
        data = make_api_request(url, timeout=20)
        if isinstance(data, dict) and data.get('status') != 'error' and not is_empty_response(data):
            return clean_dict(data)
    except Exception as e:
        print(f"New vehicle API failed: {e}")

    try:
        custom_endpoint = get_api_endpoint('vech')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, vehicle)
        else:
            url = f"{API_BASE_URL}/api/vehicle?key={API_KEY}&vehicle={vehicle}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_rc_api(vehicle):
    vehicle = vehicle.strip().upper().replace(' ', '')
    try:
        # NEW API: sahilcc.dpdns.org
        url = f"http://sahilcc.dpdns.org/api/rc?vehicle={vehicle}"
        data = make_api_request(url, timeout=20)
        if isinstance(data, dict) and data.get('status') != 'error' and not is_empty_response(data):
            return clean_dict(data)
    except Exception as e:
        print(f"New RC API failed: {e}")

    try:
        new_url = f"http://vech-to-num-production.up.railway.app/vehicle?key=Demo&number={vehicle}"
        data = make_api_request(new_url, timeout=60)
        if isinstance(data, dict) and data.get('status') != 'error' and not is_empty_response(data):
            return clean_dict(data)
    except Exception as e:
        print(f"Fallback RC API failed: {e}")

    try:
        custom_endpoint = get_api_endpoint('vechrc')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, vehicle)
        else:
            url = f"{API_BASE_URL}/api/rc?key={API_KEY}&owner={vehicle}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def save_result_to_json(command, query, result):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"result_{command}_{query}_{timestamp}.json"
        filepath = os.path.join("/tmp", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        return filepath
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return None

def send_multi_result(chat_id, message_parts, wait_message=None, json_file=None):
    if not message_parts:
        return None
    if wait_message:
        try:
            bot.delete_message(chat_id, wait_message.message_id)
        except:
            pass
    sent_messages = []
    for idx, part in enumerate(message_parts):
        markup = None
        if idx == len(message_parts) - 1 and json_file:
            file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
            JSON_FILES[file_id] = json_file
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(create_primary_button("📥 Download JSON", callback_data=f"dljson_{file_id}"))
            markup.add(create_default_button("Back", callback_data="back_to_result"))
        try:
            msg = send_with_premium(chat_id, part, reply_markup=markup)
            if msg:
                sent_messages.append(msg)
                schedule_deletion(msg.message_id, chat_id)
        except Exception as e:
            print(f"Error sending part {idx+1}: {e}")
    return sent_messages[-1] if sent_messages else None

def call_num2_api(phone):
    phone = re.sub(r'[^\d+]', '', phone).lstrip('+')
    try:
        url = f"http://node-production-1649.up.railway.app/api/telegram?key=NUMBER&id={phone}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if data.get('success') == True or data.get('status') == 'success':
                return clean_dict(data)
            return {"status": "error", "message": "NO DATA FOUND"}
        return {"status": "error", "message": "NO DATA FOUND"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def call_family_api(phone):
    phone = re.sub(r'[^\d+]', '', phone).lstrip('+')
    try:
        url = f"http://54.152.71.59:3000/search-aadhaar?search=A&aadhaar={phone}"
        data = make_api_request(url, timeout=30)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def call_ip_api(ip):
    try:
        custom_endpoint = get_api_endpoint('ip')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, ip)
        else:
            url = f"{API_BASE_URL}/api/ip?key={API_KEY}&ip={ip}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_pincode_api(pin):
    try:
        custom_endpoint = get_api_endpoint('pin')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, pin)
        else:
            url = f"{API_BASE_URL}/api/pincode?key={API_KEY}&pin={pin}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_git_api(username):
    try:
        custom_endpoint = get_api_endpoint('git')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, username)
        else:
            url = f"{API_BASE_URL}/api/git?key={API_KEY}&username={username}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_bgmi_api(uid):
    try:
        custom_endpoint = get_api_endpoint('bgmi')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, uid)
        else:
            url = f"{API_BASE_URL}/api/bgmi?key={API_KEY}&uid={uid}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_ff_api(uid):
    try:
        custom_endpoint = get_api_endpoint('ff')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, uid)
        else:
            url = f"{API_BASE_URL}/api/ff?key={API_KEY}&uid={uid}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_upi_api(upi_id):
    try:
        custom_endpoint = get_api_endpoint('upi')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, upi_id)
        else:
            url = f"{API_BASE_URL}/api/upi?key={API_KEY}&upi={upi_id}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_ifsc_api(ifsc):
    try:
        custom_endpoint = get_api_endpoint('ifsc')
        if custom_endpoint:
            url = build_api_url(custom_endpoint, ifsc)
        else:
            url = f"{API_BASE_URL}/api/ifsc?key={API_KEY}&ifsc={ifsc}"
        data = make_api_request(url, timeout=15)
        if isinstance(data, dict):
            if 'channel' in data: del data['channel']
            if is_empty_response(data):
                return {"status": "error", "message": "NO DATA FOUND"}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except:
        return {"status": "error", "message": "NO DATA FOUND"}

def call_insta_api(username):
    try:
        url = f"https://osint.invalidayushh.workers.dev/insta?key=permanent&q={username}"
        data = make_api_request(url, timeout=20)
        if isinstance(data, dict):
            if data.get('success') == False or data.get('status') == 'error':
                return {"status": "error", "message": data.get('message', 'API Error')}
            return clean_dict(data)
        return {"status": "error", "message": "NO DATA FOUND"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def format_number_result(result, query, credits_left):
    import time as _time

    divider = build_num_divider()
    e = NUM_EMOJIS

    def _err(msg_text):
        txt = (
            divider
            + f"{te(e['phone_title'], '📞')}  <b>𝗡𝗨𝗠𝗕𝗘𝗥 𝗜𝗡𝗙𝗢</b>  {te(e['phone_title'], '📞')}\n"
            + divider
            + f"\n<blockquote>"
            + f"{te(e['query'], '🔭')} Qᴜᴇʀʏ  : <code>{query}</code>\n"
            + f"{te(e['status_ok'], '❌')} {msg_text}"
            + f"</blockquote>\n\n"
            + divider
            + f"{te(e['credits'], '🧱')} Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ: <b>{credits_left}</b>\n"
            + divider
        )
        return [(txt, None)]

    if not result or result.get("status") == "error":
        return _err(result.get("message", "NO DATA FOUND") if result else "NO DATA FOUND")

    records = result.get("records", [])
    total   = result.get("total", len(records))

    if not records:
        return _err("NO DATA FOUND")

    RECORDS_PER_PAGE = 2
    pages_data = [records[i:i+RECORDS_PER_PAGE] for i in range(0, len(records), RECORDS_PER_PAGE)]
    total_pages = len(pages_data)

    start_ts = _time.time()
    out = []

    for page_idx, page_records in enumerate(pages_data):
        page_num    = page_idx + 1
        record_start = page_idx * RECORDS_PER_PAGE + 1

        txt  = divider
        txt += (
            f"{te(e['phone_title'], '📞')}  <b>𝗡𝗨𝗠𝗕𝗘𝗥 𝗜𝗡𝗙𝗢</b>  "
            f"{te(e['phone_title'], '📞')}\n"
        )
        txt += divider

        txt += (
            f"\n<blockquote>"
            f"{te(e['status_ok'], '✅')} Nᴜᴍʙᴇʀ Dᴀᴛᴀʙᴀꜱᴇ ✅\n\n"
            f"{te(e['query'],   '🔭')} Qᴜᴇʀʏ    : <code>{result.get('number', query)}</code>\n"
            f"{te(e['records'], '✍️')} Rᴇᴄᴏʀᴅꜱ  : {total} | Page {page_num}/{total_pages}"
            f"</blockquote>\n\n"
        )

        for r_idx, record in enumerate(page_records):
            abs_num = record_start + r_idx
            txt += (
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{te(e['record_badge'], '📰')} Rᴇᴄᴏʀᴅ {abs_num}/{total}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
            )

            def _field(val):
                return val if val and str(val).strip() not in ("N/A", "None", "null", "") else "—"

            txt += f"<blockquote>"
            txt += f"{te(e['number'],  '📲')} <b>Nᴜᴍʙᴇʀ</b>    : <code>{_field(record.get('mobile'))}</code>\n"
            txt += f"{te(e['name'],    '👤')} <b>Nᴀᴍᴇ</b>      : {_field(record.get('name'))}\n"
            txt += f"{te(e['father'],  '👥')} <b>Fᴀᴛʜᴇʀ</b>    : {_field(record.get('father_name'))}\n"
            txt += f"{te(e['alt_num'], '📞')} <b>Aʟᴛ Nᴜᴍ</b>   : <code>{_field(record.get('alternate'))}</code>\n"
            txt += f"{te(e['circle'],  '🔎')} <b>Cɪʀᴄʟᴇ</b>    : {_field(record.get('circle'))}\n"
            txt += f"{te(e['address'], '🏡')} <b>Aᴅᴅʀᴇꜱꜱ</b>  : {_field(record.get('address'))}\n"
            txt += f"{te(e['id_card'], '💳')} <b>Iᴅ</b>        : <code>{_field(record.get('id'))}</code>\n"
            txt += f"{te(e['email'],   '📧')} <b>Eᴍᴀɪʟ</b>     : {_field(record.get('email'))}\n"
            txt += f"</blockquote>\n\n"

        elapsed = round(_time.time() - start_ts, 2)
        bot_username = "@RAJPUT_OSINT_VIP_BOT"
        try:
            bot_username = f"@{@RAJPUT_OSINT_VIP_BOT().username}"
        except Exception:
            pass

        txt += divider
        txt += (
            f"{te(e['speed'],    '🚀')} ʀᴇꜱᴩᴏɴꜱᴇ ᴛɪᴍᴇ: {elapsed}s\n"
            f"{te(e['credits'],  '🧱')} ᴄʀᴇᴅɪᴛꜱ ʟᴇꜰᴛ: <b>{credits_left}</b>\n"
        )
        txt += divider
        txt += (
            f"{te(e['bot_icon'], '🤖')} Pᴏᴡᴇʀᴇᴅ Bʏ: <b>{bot_username}</b>  "
            f"{te(e['star'], '🌟')}\n"
        )
        txt += divider

        markup = None
        if total_pages > 1:
            markup = InlineKeyboardMarkup(row_width=3)
            buttons = []

            if page_num > 1:
                buttons.append(
                    create_primary_button(
                        "Prev",
                        callback_data=f"num_page_{page_num - 1}_{query}",
                        icon_custom_emoji_id="5246794802560774143"
                    )
                )

            buttons.append(
                create_success_button(
                    f"{page_num}/{total_pages}",
                    callback_data="num_page_noop",
                    icon_custom_emoji_id="5422537279400868395"
                )
            )

            if page_num < total_pages:
                buttons.append(
                    create_danger_button(
                        "Next",
                        callback_data=f"num_page_{page_num + 1}_{query}",
                        icon_custom_emoji_id="6192763368139397161"
                    )
                )

            markup.row(*buttons)

            if page_num == total_pages:
                markup.add(
                    InlineKeyboardButton("Download JSON", callback_data="num_dl_json")
                )

        out.append((txt, markup))

    return out
def format_aadhar_result(result, query, credits_left):
    import time as _time

    e       = ADHR_EMOJIS
    divider = build_adhr_divider()

    def _field(val):
        return val if val and str(val).strip() not in ("N/A", "None", "null", "", "—") else "—"

    def _err(msg_text):
        txt = (
            divider
            + f"{te(e['adhr_title'], '🪪')}  <b>𝗔𝗔𝗗𝗛𝗔𝗥 𝗜𝗡𝗙𝗢</b>  {te(e['adhr_title'], '🪪')}\n"
            + divider
            + f"\n<blockquote>"
            + f"{te(e['query'], '🔭')} <b>Qᴜᴇʀʏ</b>  : <code>{query}</code>\n"
            + f"{te(e['status_ok'], '❌')} {msg_text}"
            + f"</blockquote>\n\n"
            + divider
            + f"{te(e['credits'], '📊')} <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: {credits_left}\n"
            + divider
        )
        return [(txt, None)]

    if not result or result.get("status") == "error":
        return _err(result.get("message", "NO DATA FOUND") if result else "NO DATA FOUND")

    records = result.get("records", [])
    total   = result.get("total", len(records))

    if not records:
        return _err("NO DATA FOUND")

    RECORDS_PER_PAGE = 4
    pages_data  = [records[i:i + RECORDS_PER_PAGE] for i in range(0, len(records), RECORDS_PER_PAGE)]
    total_pages = len(pages_data)
    start_ts    = _time.time()
    out         = []

    for page_idx, page_records in enumerate(pages_data):
        page_num     = page_idx + 1
        record_start = page_idx * RECORDS_PER_PAGE + 1

        # ── header ──
        txt  = divider
        txt += f"{te(e['adhr_title'], '🪪')}  <b>𝗔𝗔𝗗𝗛𝗔𝗥 𝗜𝗡𝗙𝗢</b>  {te(e['adhr_title'], '🪪')}\n"
        txt += divider
        txt += (
            f"<blockquote>"
            f"{te(e['status_ok'], '✅')} Aᴀᴅʜᴀʀ Dᴀᴛᴀʙᴀꜱᴇ ✅\n\n"
            f"{te(e['query'],   '🔭')} <b>Qᴜᴇʀʏ</b>   : <code>{query}</code>\n"
            f"{te(e['records'], '✍️')} <b>Rᴇᴄᴏʀᴅꜱ</b> : {total} | Page {page_num}/{total_pages}"
            f"</blockquote>\n\n"
        )

        # ── records ──
        for r_idx, record in enumerate(page_records):
            abs_num   = record_start + r_idx
            email_val = _field(record.get('email'))

            txt += (
                f"<blockquote>"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{te(e['record_badge'], '📰')} <b>Rᴇᴄᴏʀᴅ {abs_num}/{total}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"{te(e['mobile'],  '📲')} <b>Mᴏʙɪʟᴇ</b>   : <code>{_field(record.get('mobile'))}</code>\n"
                f"{te(e['name'],    '👤')} <b>Nᴀᴍᴇ</b>     : {_field(record.get('name'))}\n"
                f"{te(e['father'],  '👥')} <b>Fᴀᴛʜᴇʀ</b>   : {_field(record.get('father_name'))}\n"
                f"{te(e['circle'],  '🛜')} <b>Cɪʀᴄʟᴇ</b>   : {_field(record.get('circle'))}\n"
                f"{te(e['address'], '🏡')} <b>Aᴅᴅʀᴇꜱꜱ</b> : {_field(record.get('address'))}\n"
                f"{te(e['id_card'], '💳')} <b>Aᴀᴅʜᴀᴀʀ</b>  : <code>{_field(record.get('aadhar'))}</code>\n"
                + (f"{te(e['email'], '📧')} <b>Eᴍᴀɪʟ</b>    : {email_val}\n" if email_val != "—" else "")
                + f"</blockquote>\n\n"
            )

        # ── footer ──
        elapsed      = round(_time.time() - start_ts, 2)
        bot_username = "@RAJPUT_OSINT_VIP_BOT"
        try:
            bot_username = f"@{@RAJPUT_OSINT_VIP_BOT().username}"
        except Exception:
            pass

        txt += divider
        txt += (
            f"<blockquote>"
            f"{te(e['speed'],    '🚀')} <b>ʀᴇꜱᴩᴏɴꜱᴇ ᴛɪᴍᴇ</b>:- {elapsed}s\n"
            f"{te(e['credits'],  '📊')} <b>ᴄʀᴇᴅɪᴛꜱ ʟᴇꜰᴛ</b>:- {credits_left}\n"
            f"</blockquote>\n"
        )
        txt += divider
        txt += (
            f"<blockquote>"
            f"{te(e['bot_icon'], '🤖')} Pᴏᴡᴇʀᴇᴅ Bʏ: <b>{bot_username}</b>  {te(e['star'], '🌟')}\n"
            f"</blockquote>\n"
        )
        txt += divider

        # ── pagination buttons ──
        markup = None
        if total_pages > 1:
            markup  = InlineKeyboardMarkup(row_width=3)
            buttons = []
            if page_num > 1:
                buttons.append(create_primary_button(
                    "Prev",
                    callback_data=f"num_page_{page_num - 1}_{query}",
                    icon_custom_emoji_id="5246794802560774143"
                ))
            buttons.append(create_success_button(
                f"{page_num}/{total_pages}",
                callback_data="num_page_noop",
                icon_custom_emoji_id="5422537279400868395"
            ))
            if page_num < total_pages:
                buttons.append(create_danger_button(
                    "Next",
                    callback_data=f"num_page_{page_num + 1}_{query}",
                    icon_custom_emoji_id="6192763368139397161"
                ))
            markup.row(*buttons)
            if page_num == total_pages:
                markup.add(InlineKeyboardButton("Download JSON", callback_data="num_dl_json"))

        out.append((txt, markup))

    return out


# ============================================================
# VEHICLE / RC FORMATTER WITH PAGINATION
# ============================================================

VECH_PAGINATION = {}   # user_id -> {"pages": [str], "current": int, "query": str, "json_file": str}

def _vfield(data, *keys, default="N/A"):
    """Safely extract nested dict values."""
    for k in keys:
        if isinstance(data, dict):
            data = data.get(k)
        else:
            return default
    return data if data is not None and str(data).strip() not in ("", "None", "null", "N/A") else default

def _vfmt(val):
    return str(val) if val and str(val).strip() not in ("", "None", "null", "N/A", "—") else "N/A"

def format_vehicle_result_v2(result, query, credits_left):
    """Format /vech response — parses nested API structure."""
    import time as _time
    e = VECH_EMOJIS
    divider = build_vech_divider()

    def _err(msg_text):
        txt = (
            divider
            + f"{te(e['veh_title'], '🪪')}  <b>𝗩𝗘𝗛𝗜𝗖𝗟𝗘 𝗜𝗡𝗙𝗢</b>  {te(e['veh_title'], '🪪')}\n"
            + divider
            + f"\n<blockquote>"
            + f"{te(e['query'], '🔭')} <b>Qᴜᴇʀʏ</b>  : <code>{query}</code>\n"
            + f"{te(e['status_ok'], '❌')} {msg_text}"
            + f"</blockquote>\n\n"
            + divider
            + f"{te(e['credits'], '🧱')} <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: {credits_left}\n"
            + divider
        )
        return [txt]

    if not result or result.get("status") == "error":
        return _err(result.get("message", "NO DATA FOUND") if result else "NO DATA FOUND")

    # ── extract nested /vech data ──
    d = result
    if "result" in result and isinstance(result["result"], dict):
        d = result["result"]
    if "data" in d and isinstance(d["data"], dict):
        d = d["data"]

    mobile = ""
    if isinstance(d, dict):
        mobile = str(d.get("mobile", "")).strip()

    # api1 source1 details
    s1 = {}
    try:
        s1 = d["vehicle_info"]["results"]["api1"]["result"]["source1"]["details"]
    except Exception:
        pass

    # api1 source2 nexus
    s2 = {}
    try:
        s2 = d["vehicle_info"]["results"]["api1"]["result"]["source2"]["data"]["Nexus2"]
    except Exception:
        pass

    # api2 detailed data
    a2 = {}
    try:
        a2 = d["vehicle_info"]["results"]["api2"]["data"]["data"]
    except Exception:
        pass

    def _g(*keys, srcs=(s1, s2, a2), default="N/A"):
        for src in srcs:
            if not isinstance(src, dict):
                continue
            val = src
            for k in keys:
                if isinstance(val, dict):
                    val = val.get(k)
                else:
                    val = None
                    break
            if val is not None and str(val).strip() not in ("", "None", "null", "N/A", "—"):
                return str(val).strip()
        return default

    def _g2(key, srcs=(s1, s2, a2), default="N/A"):
        for src in srcs:
            if not isinstance(src, dict):
                continue
            for k in (key, " " + key, key + " ", " " + key + " "):
                if k in src:
                    v = src[k]
                    if v is not None and str(v).strip() not in ("", "None", "null", "N/A", "—"):
                        return str(v).strip()
        return default

    rc_num      = _g("regNo", "rc", "vehicleNumber", default=query)
    make        = _g2("Model Name", default=_g("vehicleManufacturerName", "make_display_name"))
    model       = _g2("Model Name", default=_g("vehicleManufacturerName"))
    mfg_year    = _g("vehicleManufacturingMonthYear", "mfgDate")
    fuel        = _g2("Fuel Type", default=_g("fuelType", "type"))
    vclass      = _g2("Vehicle Class", default=_g("vehicleClass", "vehicleCategory"))
    cc_val      = _g("vehicleCubicCapacity", "cubic_capacity", "vehicleCylindersNo")
    seating     = _g("vehicleSeatCapacity", "seating_capacity", "seats")
    colour      = _g("vehicleColour", "vehicle_color", "color")
    body        = _g("bodyType", "body")

    owner_name = "N/A"
    for src in (s1, s2):
        if isinstance(src, dict):
            for k in (" Name", "Name", "owner", "ownerName"):
                if k in src:
                    v = src[k]
                    if v and str(v).strip() not in ("", "None", "null", "N/A"):
                        owner_name = str(v).strip()
                        break
            if owner_name != "N/A":
                break

    mobile_num  = mobile if mobile else _g2("Phone")
    address     = _g2("Address", default=_g("presentAddress", "permanentAddress", "Address"))

    reg_date    = _g2("Registration Date", default=_g("regDate", "rcDate"))
    rto_name    = _g2("Registered RTO", default=_g("regAuthority"))
    rto_code    = _g("rtoCode")
    financer    = _g("rcFinancer", "financed")
    rto_city    = _g2("City Name")
    rto_phone   = _g2("Phone")
    rc_status   = _g("status")
    tax_upto    = _g("vehicleTaxUpto", "Tax Upto")
    commercial  = "Yes" if _g("isCommercial") in ("true", "True", True, "yes", "Yes") else "No"

    ins_status  = "Active" if _g("vehicleInsuranceUpto", "Insurance Upto") not in ("N/A", "", "Expired") else "Expired"
    ins_company = _g2("Insurance Company", default=_g("vehicleInsuranceCompanyName"))
    policy_no   = _g2("Insurance No", default=_g("vehicleInsurancePolicyNumber", "insurancePolicyNumber"))
    ins_valid   = _g2("Insurance Upto", default=_g("vehicleInsuranceUpto", "insuranceUpto"))

    chassis_no  = _g("chassis", "chassis_number", "Chassis Number")
    engine_no   = _g("engine", "engine_number", "Engine Number")
    norms_val   = _g("normsType", "norms_desc", "emission_norms")

    start_ts = _time.time()

    # ── build lines ──
    lines = []
    lines.append(divider)
    lines.append(f"{te(e['veh_title'], '🪪')}  <b>𝗩𝗘𝗛𝗜𝗖𝗟𝗘 𝗜𝗡𝗙𝗢</b>  {te(e['veh_title'], '🪪')}")
    lines.append(divider)
    lines.append("")
    lines.append(f"{te(e['rc_number'], '🚗')} <b>Rᴄ Nᴜᴍʙᴇʀ</b>  : <code>{rc_num}</code>")
    lines.append(f"{te(e['source'], '💎')} <b>Sᴏᴜʀᴄᴇ</b>    : ꜰᴇʟɪxᴀᴩɪ {te(e['status_ok'], '✅')}")
    lines.append("")

    # Vehicle Details section
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['vehicle'], '🚗')} <b>Vᴇʜɪᴄʟᴇ Dᴇᴛᴀɪʟꜱ</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['make'], '🏭')} <b>Mᴀᴋᴇ</b>         : {make}")
    lines.append(f"  {te(e['vehicle'], '🚗')} <b>Mᴏᴅᴇʟ</b>        : {model}")
    lines.append(f"  {te(e['mfg_year'], '🗓️')} <b>Mꜰɢ ʏᴇᴀʀ</b>     : {mfg_year}")
    lines.append(f"  {te(e['fuel'], '⚡️')} <b>Fᴜᴇʟ</b>         : {fuel}")
    lines.append(f"  {te(e['vclass'], '👿')} <b>Cʟᴀꜱꜱ</b>         : {vclass}")
    lines.append(f"  {te(e['cc'], '⚙️')} <b>Cᴄ</b>            : {cc_val}")
    lines.append(f"  {te(e['seating'], '🐸')} <b>Sᴇᴀᴛɪɴɢ</b>      : {seating}")
    lines.append(f"  {te(e['colour'], '📋')} <b>Cᴏʟᴏᴜʀ</b>       : {colour}")
    lines.append(f"  {te(e['body'], '🏎')} <b>Bᴏᴅʏ</b>         : {body}")
    lines.append("")

    # Owner Info section
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['body'], '🏎')} <b>Oᴡɴᴇʀ Iɴꜰᴏ</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['owner'], '👨‍🦰')} <b>Nᴀᴍᴇ</b>         : {owner_name}")
    lines.append(f"  {te(e['mobile'], '📲')} <b>Mᴏʙɪʟᴇ</b>       : <code>{mobile_num}</code>")
    lines.append(f"  {te(e['address'], '🏡')} <b>Aᴅᴅʀᴇꜱꜱ</b>      : {address}")
    lines.append("")

    # Registration section
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['registration'], '0️⃣')} <b>𝗥𝗘𝗚𝗜𝗦𝗧𝗥𝗔𝗧𝗜𝗢𝗡</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['reg_date'], '🗓️')} <b>Rᴇɢ Dᴀᴛᴇ</b>     : {reg_date}")
    lines.append(f"  {te(e['rto'], '🗺')} <b>Rᴛᴏ</b>           : {rto_name}")
    lines.append(f"  {te(e['rto_code'], '🔢')} <b>Rᴛᴏ ᴄᴏᴅᴇ</b>    : {rto_code}")
    lines.append(f"  {te(e['financer'], '🏢')} <b>Fɪɴᴀɴᴄᴇʀ</b>     : {financer}")
    lines.append(f"  {te(e['rto'], '🗺')} <b>Rᴛᴏ Cɪᴛʏ</b>    : {rto_city}")
    lines.append(f"  {te(e['mobile'], '📲')} <b>Rᴛᴏ Pʜᴏɴᴇ</b>   : {rto_phone}")
    lines.append(f"  {te(e['status_ok'], '✅')} <b>Rᴄ Sᴛᴀᴛᴜꜱ</b>   : {rc_status}")
    lines.append(f"  {te(e['reg_date'], '🗓️')} <b>Tᴀx Uᴩᴛᴏ</b>    : {tax_upto}")
    lines.append(f"  {te(e['commercial'], '💎')} <b>Cᴏᴍᴍᴇʀᴄɪᴀʟ</b>  : {commercial}")
    lines.append("")

    # Insurance section
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['insurance'], '🏎')} <b>𝗜𝗡𝗦𝗨𝗥𝗔𝗡𝗖𝗘</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['ins_status'], '🛡')} <b>Sᴛᴀᴛᴜꜱ</b>        : {ins_status}")
    lines.append(f"  {te(e['financer'], '🏢')} <b>Cᴏᴍᴩᴀɴʏ</b>      : {ins_company}")
    lines.append(f"  {te(e['colour'], '📋')} <b>Pᴏʟɪᴄʏ ɴᴏ.</b>  : <code>{policy_no}</code>")
    lines.append(f"  {te(e['reg_date'], '🗓️')} <b>Vᴀʟɪᴅ ᴛɪʟ</b>    : {ins_valid}")
    lines.append("")

    # Technical section
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['technical'], '⚙️')} <b>𝗧𝗘𝗖𝗛𝗡𝗜𝗖𝗔𝗟</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['chassis'], '🔧')} <b>Cʜᴀꜱꜱɪꜱ</b>     : <code>{chassis_no}</code>")
    lines.append(f"  {te(e['engine'], '⚙️')} <b>Eɴɢɪɴᴇ</b>       : <code>{engine_no}</code>")
    lines.append(f"  {te(e['norms'], '⚙️')} <b>Nᴏʀᴍꜱ</b>         : {norms_val}")
    lines.append("")

    # Footer
    elapsed = round(_time.time() - start_ts, 2)
    try:
        bot_username = f"@{@RAJPUT_OSINT_VIP_BOT().username}"
    except Exception:
        bot_username = "@RAJPUT_OSINT_VIP_BOT"

    lines.append(f"{te(e['credits'], '🧱')} <b>ᴄʀᴇᴅɪᴛꜱ ʟᴇꜰᴛ</b>:- {credits_left}")
    lines.append(divider)
    lines.append(f"{te(e['bot_icon'], '🤖')} <b>Pᴏᴡᴇʀᴇᴅ Bʏ</b>: <b>{bot_username}</b>  {te(e['star'], '🌟')}")
    lines.append(divider)

    full_text = "\n".join(lines)

    # ── paginate: single blockquote per page, split at section boundaries ──
    # Check length including blockquote tags
    wrapped = f"<blockquote>{full_text}</blockquote>"
    if len(wrapped) <= 4096 and len(full_text) <= 3500:
        return [wrapped]

    # Split at section boundaries (search for plain text markers, not raw emojis)
    sec_markers = [
        "━━━━━━━━━━━━━━━━━━━━━\n  🏭 <b>Mᴀᴋᴇ</b>",         # vehicle details start
        "━━━━━━━━━━━━━━━━━━━━━\n  👨‍🦰 <b>Nᴀᴍᴇ</b>",         # owner info start
        "━━━━━━━━━━━━━━━━━━━━━\n  🗓️ <b>Rᴇɢ Dᴀᴛᴇ</b>",     # registration start
        "━━━━━━━━━━━━━━━━━━━━━\n  🛡 <b>Sᴛᴀᴛᴜꜱ</b>",        # insurance start
        "━━━━━━━━━━━━━━━━━━━━━\n  🔧 <b>Cʜᴀꜱꜱɪꜱ</b>",      # technical start
        "🧱 <b>ᴄʀᴇᴅɪᴛꜱ ʟᴇꜰᴛ</b>",                           # footer start
    ]

    # Find all split positions
    split_positions = [0]
    for marker in sec_markers:
        pos = full_text.find(marker)
        if pos != -1 and pos not in split_positions:
            split_positions.append(pos)
    split_positions.sort()
    split_positions.append(len(full_text))

    # Build pages from split positions
    pages = []
    for i in range(len(split_positions) - 1):
        page_text = full_text[split_positions[i]:split_positions[i+1]].rstrip("\n")
        if page_text:
            pages.append(page_text)

    # Merge small pages if possible
    merged = []
    current = ""
    for page in pages:
        test = current + ("\n" if current else "") + page
        if len(test) <= 1024:
            current = test
        else:
            if current:
                merged.append(current)
            current = page
    if current:
        merged.append(current)

    final_pages = []
    for i, page in enumerate(merged, 1):
        if len(merged) > 1:
            page += f"\n{te(e['records'], '✍️')} <b>Page {i}/{len(merged)}</b>"
        final_pages.append(f"<blockquote>{page}</blockquote>")

    return final_pages if final_pages else [f"<blockquote>{full_text}</blockquote>"]


def format_rc_result_v2(result, query, credits_left):
    """Format /vechrc response — parses flat sectioned JSON."""
    import time as _time
    e = VECH_EMOJIS
    divider = build_vech_divider()

    def _err(msg_text):
        txt = (
            divider
            + f"{te(e['veh_title'], '🪪')}  <b>𝗥𝗖 𝗜𝗡𝗙𝗢</b>  {te(e['veh_title'], '🪪')}\n"
            + divider
            + f"\n<blockquote>"
            + f"{te(e['query'], '🔭')} <b>Qᴜᴇʀʏ</b>  : <code>{query}</code>\n"
            + f"{te(e['status_ok'], '❌')} {msg_text}"
            + f"</blockquote>\n\n"
            + divider
            + f"{te(e['credits'], '🧱')} <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: {credits_left}\n"
            + divider
        )
        return [txt]

    if not result or result.get("status") == "error":
        return _err(result.get("message", "NO DATA FOUND") if result else "NO DATA FOUND")

    d = result
    if "result" in result and isinstance(result["result"], dict):
        d = result["result"]

    def _sec(name):
        return d.get(name, {}) if isinstance(d, dict) else {}

    def _v(val, default="N/A"):
        return str(val).strip() if val is not None and str(val).strip() not in ("", "None", "null", "N/A", "—") else default

    own = _sec("Ownership Details")
    veh = _sec("Vehicle Details")
    ins = _sec("Insurance Information")
    dates = _sec("Important Dates & Validity")
    other = _sec("Other Information")
    card = _sec("Basic Card Info")
    alert = _sec("Insurance Alert")
    reg_num = _v(d.get("registration_number", query))

    rc_num      = _v(own.get("Registration Number", reg_num))
    owner_name  = _v(own.get("Owner Name", card.get("Owner Name")))
    rto_name    = _v(own.get("Registered RTO"))

    make        = _v(veh.get("Model Name", card.get("Modal Name")))
    model       = _v(veh.get("Maker Model", veh.get("Model Name")))
    vclass      = _v(veh.get("Vehicle Class"))
    fuel        = _v(veh.get("Fuel Type"))
    chassis_no  = _v(veh.get("Chassis Number"))
    engine_no   = _v(veh.get("Engine Number"))

    ins_expiry  = _v(ins.get("Insurance Expiry", ins.get("If your insurance has expired, renew it")))
    ins_company = _v(ins.get("Insurance Company"))
    policy_no   = _v(ins.get("Insurance No"))

    reg_date    = _v(dates.get("Registration Date"))
    vehicle_age = _v(dates.get("Vehicle Age"))
    fitness     = _v(dates.get("Fitness Upto"))
    ins_upto    = _v(dates.get("Insurance Upto"))
    ins_alert   = _v(dates.get("Insurance Expiry In"))

    financer    = _v(other.get("Financer Name"))
    cc_val      = _v(other.get("Cubic Capacity"))
    seating     = _v(other.get("Seating Capacity"))
    permit      = _v(other.get("Permit Type"))
    blacklist   = _v(other.get("Blacklist Status"))
    noc         = _v(other.get("NOC Details"))

    city        = _v(card.get("City Name"))
    phone       = _v(card.get("Phone"))
    website     = _v(card.get("Website"))
    address     = _v(card.get("Address"))
    code        = _v(card.get("Code"))

    expired_days = _v(alert.get("Expired Days"))

    start_ts = _time.time()

    lines = []
    lines.append(divider)
    lines.append(f"{te(e['veh_title'], '🪪')}  <b>𝗥𝗖 𝗜𝗡𝗙𝗢</b>  {te(e['veh_title'], '🪪')}")
    lines.append(divider)
    lines.append("")
    lines.append(f"{te(e['rc_number'], '🚗')} <b>Rᴄ Nᴜᴍʙᴇʀ</b>  : <code>{rc_num}</code>")
    lines.append(f"{te(e['source'], '💎')} <b>Sᴏᴜʀᴄᴇ</b>    : ꜰᴇʟɪxᴀᴩɪ {te(e['status_ok'], '✅')}")
    lines.append("")

    # Vehicle Details
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['vehicle'], '🚗')} <b>Vᴇʜɪᴄʟᴇ Dᴇᴛᴀɪʟꜱ</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['make'], '🏭')} <b>Mᴀᴋᴇ</b>         : {make}")
    lines.append(f"  {te(e['vehicle'], '🚗')} <b>Mᴏᴅᴇʟ</b>        : {model}")
    lines.append(f"  {te(e['vclass'], '👿')} <b>Cʟᴀꜱꜱ</b>         : {vclass}")
    lines.append(f"  {te(e['fuel'], '⚡️')} <b>Fᴜᴇʟ</b>         : {fuel}")
    lines.append(f"  {te(e['cc'], '⚙️')} <b>Cᴄ</b>            : {cc_val}")
    lines.append(f"  {te(e['seating'], '🐸')} <b>Sᴇᴀᴛɪɴɢ</b>      : {seating}")
    lines.append(f"  {te(e['chassis'], '🔧')} <b>Cʜᴀꜱꜱɪꜱ</b>     : <code>{chassis_no}</code>")
    lines.append(f"  {te(e['engine'], '⚙️')} <b>Eɴɢɪɴᴇ</b>       : <code>{engine_no}</code>")
    lines.append("")

    # Owner Info
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['body'], '🏎')} <b>Oᴡɴᴇʀ Iɴꜰᴏ</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['owner'], '👨‍🦰')} <b>Nᴀᴍᴇ</b>         : {owner_name}")
    lines.append(f"  {te(e['address'], '🏡')} <b>Aᴅᴅʀᴇꜱꜱ</b>      : {address}")
    lines.append(f"  {te(e['rto'], '🗺')} <b>Cɪᴛʏ</b>          : {city}")
    lines.append(f"  {te(e['mobile'], '📲')} <b>Pʜᴏɴᴇ</b>        : {phone}")
    lines.append("")

    # Registration
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['registration'], '0️⃣')} <b>𝗥𝗘𝗚𝗜𝗦𝗧𝗥𝗔𝗧𝗜𝗢𝗡</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['reg_date'], '🗓️')} <b>Rᴇɢ Dᴀᴛᴇ</b>     : {reg_date}")
    lines.append(f"  {te(e['rto'], '🗺')} <b>Rᴛᴏ</b>           : {rto_name}")
    lines.append(f"  {te(e['rto_code'], '🔢')} <b>Rᴛᴏ Cᴏᴅᴇ</b>    : {code}")
    lines.append(f"  {te(e['financer'], '🏢')} <b>Fɪɴᴀɴᴄᴇʀ</b>     : {financer}")
    lines.append(f"  {te(e['reg_date'], '🗓️')} <b>Fɪᴛɴᴇꜱꜱ Uᴘᴛᴏ</b> : {fitness}")
    lines.append(f"  {te(e['status_ok'], '✅')} <b>Bʟᴀᴄᴋʟɪꜱᴛ</b>   : {blacklist}")
    lines.append(f"  {te(e['status_ok'], '✅')} <b>NOC</b>          : {noc}")
    lines.append(f"  {te(e['reg_date'], '🗓️')} <b>Vᴇʜɪᴄʟᴇ Aɢᴇ</b>  : {vehicle_age}")
    lines.append("")

    # Insurance
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['insurance'], '🏎')} <b>𝗜𝗡𝗦𝗨𝗥𝗔𝗡𝗖𝗘</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['ins_status'], '🛡')} <b>Sᴛᴀᴛᴜꜱ</b>        : {ins_alert}")
    lines.append(f"  {te(e['financer'], '🏢')} <b>Cᴏᴍᴩᴀɴʏ</b>      : {ins_company}")
    lines.append(f"  {te(e['colour'], '📋')} <b>Pᴏʟɪᴄʏ ɴᴏ.</b>  : <code>{policy_no}</code>")
    lines.append(f"  {te(e['reg_date'], '🗓️')} <b>Eхᴘɪʀʏ</b>       : {ins_expiry}")
    lines.append(f"  {te(e['reg_date'], '🗓️')} <b>Eхᴘɪʀᴇᴅ Dᴀʏꜱ</b> : {expired_days}")
    lines.append("")

    # Other Info
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"{te(e['technical'], '⚙️')} <b>𝗢𝗧𝗛𝗘𝗥 𝗜𝗡𝗙𝗢</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"  {te(e['commercial'], '💎')} <b>Pᴇʀᴍɪᴛ</b>       : {permit}")
    lines.append(f"  {te(e['rto'], '🗺')} <b>Wᴇʙꜱɪᴛᴇ</b>      : {website}")
    lines.append("")

    # Footer
    elapsed = round(_time.time() - start_ts, 2)
    try:
        bot_username = f"@{bot.get_me().username}"
    except Exception:
        bot_username = "@RAJPUT_OSINT_VIP_BOT"

    lines.append(f"{te(e['credits'], '🧱')} <b>ᴄʀᴇᴅɪᴛꜱ ʟᴇꜰᴛ</b>:- {credits_left}")
    lines.append(divider)
    lines.append(f"{te(e['bot_icon'], '🤖')} <b>Pᴏᴡᴇʀᴇᴅ Bʏ</b>: <b>{bot_username}</b>  {te(e['star'], '🌟')}")
    lines.append(divider)

    full_text = "\n".join(lines)

    wrapped = f"<blockquote>{full_text}</blockquote>"
    if len(wrapped) <= 4096 and len(full_text) <= 3500:
        return [wrapped]

    # Split at section boundaries
    sec_markers = [
        "━━━━━━━━━━━━━━━━━━━━━\n  🏭 <b>Mᴀᴋᴇ</b>",         # vehicle details start
        "━━━━━━━━━━━━━━━━━━━━━\n  👨‍🦰 <b>Nᴀᴍᴇ</b>",         # owner info start
        "━━━━━━━━━━━━━━━━━━━━━\n  🗓️ <b>Rᴇɢ Dᴀᴛᴇ</b>",     # registration start
        "━━━━━━━━━━━━━━━━━━━━━\n  🛡 <b>Sᴛᴀᴛᴜꜱ</b>",        # insurance start
        "━━━━━━━━━━━━━━━━━━━━━\n  💎 <b>Pᴇʀᴍɪᴛ</b>",        # other info start
        "🧱 <b>ᴄʀᴇᴅɪᴛꜱ ʟᴇꜰᴛ</b>",                           # footer start
    ]

    split_positions = [0]
    for marker in sec_markers:
        pos = full_text.find(marker)
        if pos != -1 and pos not in split_positions:
            split_positions.append(pos)
    split_positions.sort()
    split_positions.append(len(full_text))

    pages = []
    for i in range(len(split_positions) - 1):
        page_text = full_text[split_positions[i]:split_positions[i+1]].rstrip("\n")
        if page_text:
            pages.append(page_text)

    merged = []
    current = ""
    for page in pages:
        test = current + ("\n" if current else "") + page
        if len(test) <= 1024:
            current = test
        else:
            if current:
                merged.append(current)
            current = page
    if current:
        merged.append(current)

    final_pages = []
    for i, page in enumerate(merged, 1):
        if len(merged) > 1:
            page += f"\n{te(e['records'], '✍️')} <b>Page {i}/{len(merged)}</b>"
        final_pages.append(f"<blockquote>{page}</blockquote>")

    return final_pages if final_pages else [f"<blockquote>{full_text}</blockquote>"]


def send_paginated_vech(chat_id, user_id, pages, json_file, query, wait_message=None, command="vech"):
    """Send paginated vehicle/RC result with Prev/Next buttons."""
    if wait_message:
        try:
            bot.delete_message(chat_id, wait_message.message_id)
        except:
            pass

    VECH_PAGINATION[user_id] = {
        "pages": pages,
        "current": 0,
        "query": query,
        "json_file": json_file,
        "command": command,
    }

    _send_vech_page(chat_id, user_id, 0)


def _send_vech_page(chat_id, user_id, page_idx):
    state = VECH_PAGINATION.get(user_id)
    if not state:
        return

    pages = state["pages"]
    if page_idx < 0 or page_idx >= len(pages):
        return

    state["current"] = page_idx
    text = pages[page_idx]

    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []

    if len(pages) > 1:
        if page_idx > 0:
            buttons.append(create_primary_button(
                "◀ Prev",
                callback_data=f"vech_page_{page_idx - 1}_{user_id}",
                icon_custom_emoji_id="5246794802560774143"
            ))

        buttons.append(create_success_button(
            f"{page_idx + 1}/{len(pages)}",
            callback_data=f"vech_noop_{user_id}",
            icon_custom_emoji_id="5422537279400868395"
        ))

        if page_idx < len(pages) - 1:
            buttons.append(create_danger_button(
                "Next ▶",
                callback_data=f"vech_page_{page_idx + 1}_{user_id}",
                icon_custom_emoji_id="6192763368139397161"
            ))

        markup.row(*buttons)

    # JSON download on last page
    json_file = state.get("json_file")
    if page_idx == len(pages) - 1 and json_file:
        file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
        JSON_FILES[file_id] = json_file
        markup.add(InlineKeyboardButton("📥 Download JSON", callback_data=f"dljson_{file_id}"))

    markup.add(create_default_button("🔙 Back", callback_data="back_to_result"))

    sent = send_with_premium(chat_id, text, reply_markup=markup)
    if sent:
        schedule_deletion(sent.message_id, chat_id)
        send_random_media(chat_id, sent.message_id)

def format_tgid_result(result, query, credits_left):
    e = NUM_EMOJIS
    divider = build_num_divider()
    lines = []

    if isinstance(result, dict) and result.get('status') == 'error':
        lines.append(divider)
        lines.append(te(e['phone_title'], '📞') + "  <b>𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠 𝗜𝗡𝗙𝗢</b>  " + te(e['phone_title'], '📞'))
        lines.append(divider)
        lines.append("")
        lines.append("<blockquote>")
        lines.append(te(e['query'], '🔭') + " <b>Qᴜᴇʀʏ</b>  : <code>" + str(query) + "</code>")
        lines.append(te(e['status_ok'], '❌') + " " + str(result.get('message', 'NO DATA FOUND')))
        lines.append("</blockquote>")
        lines.append("")
        lines.append(divider)
        lines.append(te(e['credits'], '🧱') + " <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: " + str(credits_left))
        lines.append(divider)
        return chr(10).join(lines)

    if result.get('status') == 'success':
        msg_text = result.get('msg', '')
        q = result.get('query', query)
        query_type = '🆔 User ID' if str(q).isdigit() else '👤 Username'
        note = result.get('note', '')
        tgid = result.get('tgid', 'N/A')
        username = result.get('username', 'N/A')
        phone = result.get('phone', 'N/A')
        country = result.get('country', 'N/A')
        country_code = result.get('country_code', 'N/A')

        lines.append(divider)
        lines.append(te(e['phone_title'], '📞') + "  <b>𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠 𝗜𝗡𝗙𝗢</b>  " + te(e['phone_title'], '📞'))
        lines.append(divider)
        lines.append("")
        lines.append("<blockquote>")
        lines.append(te(e['query'], '🔭') + " <b>Qᴜᴇʀʏ</b>    : <code>" + str(q) + "</code>")
        type_line = te(e['status_ok'], '🔍') + " <b>Tʏᴘᴇ</b>     : " + query_type
        if note:
            type_line += chr(10) + te(e['status_ok'], '💡') + " <b>Nᴏᴛᴇ</b>: " + note
        lines.append(type_line)
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        if tgid != 'N/A':
            lines.append(te(e['id_card'], '🆔') + " <b>TG ID</b>         : <code>" + str(tgid) + "</code>")
        if username != 'N/A':
            lines.append(te(e['name'], '👤') + " <b>Uꜱᴇʀɴᴀᴍᴇ</b>     : @" + str(username))
        if phone != 'N/A':
            lines.append(te(e['number'], '📲') + " <b>Pʜᴏɴᴇ</b>        : <code>" + str(phone) + "</code>")
        if country != 'N/A':
            lines.append(te(e['circle'], '🔎') + " <b>Cᴏᴜɴᴛʀʏ</b>      : " + str(country))
        if country_code != 'N/A':
            lines.append(te(e['alt_num'], '📞') + " <b>Cᴏᴜɴᴛʀʏ Cᴏᴅᴇ</b> : " + str(country_code))
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        if msg_text and msg_text != 'Details fetched':
            lines.append(te(e['status_ok'], '✅') + " <b>Sᴛᴀᴛᴜꜱ</b>: " + msg_text)
        lines.append("</blockquote>")
        lines.append("")
        lines.append(divider)
        lines.append(te(e['credits'], '🧱') + " <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: " + str(credits_left))
        lines.append(divider)
        return chr(10).join(lines)

    lines.append(divider)
    lines.append(te(e['phone_title'], '📞') + "  <b>𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠 𝗜𝗡𝗙𝗢</b>  " + te(e['phone_title'], '📞'))
    lines.append(divider)
    lines.append("")
    lines.append("<blockquote>")
    lines.append(te(e['query'], '🔭') + " <b>Qᴜᴇʀʏ</b>  : <code>" + str(query) + "</code>")
    lines.append(te(e['status_ok'], '❌') + " NO DATA FOUND")
    lines.append("</blockquote>")
    lines.append("")
    lines.append(divider)
    lines.append(te(e['credits'], '🧱') + " <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: " + str(credits_left))
    lines.append(divider)
    return chr(10).join(lines)

def format_api_result(result, title, query, credits_left):
    if isinstance(result, dict) and result.get('status') == 'error' and result.get('message') == 'NO DATA FOUND':
        msg = f"""
<blockquote>{title}</blockquote>

<blockquote>Query: {query}
❌ NO DATA FOUND</blockquote>

💰 Credits Left: {credits_left}
"""
        return msg

    SKIP_KEYS = {'status', 'channel', 'by', 'owner', 'credit', 'message', 'success', 'latency',
                 'response_metadata', 'makeData', 'modelData', 'variant', 'less_info', 'masked_name',
                 'developer', 'contact', 'tag', 'key_expiry'}

    DISPLAY_NAMES = {
        'rc_number': 'RC Number', 'registration_number': 'Registration Number',
        'fit_up_to': 'Fitness Valid Upto', 'registration_date': 'Registration Date',
        'owner_name': 'Owner Name', 'father_name': 'Father Name',
        'present_address': 'Present Address', 'mobile_number': 'Mobile Number',
        'vehicle_category': 'Vehicle Category', 'fuel_type': 'Fuel Type', 'color': 'Color',
        'insurance_company': 'Insurance Company', 'manufacturing_date': 'Manufacturing Date',
        'registered_at': 'Registered RTO', 'tax_upto': 'Tax Valid Upto',
        'user_id': 'User ID', 'username': 'Username', 'first_name': 'Name',
        'phone': 'Phone Number', 'email': 'Email', 'address': 'Address',
        'city': 'City', 'state': 'State', 'country': 'Country',
        'pincode': 'Pincode', 'pan': 'PAN Number', 'aadhar': 'Aadhar Number',
        'upi': 'UPI ID', 'ifsc': 'IFSC Code', 'bank': 'Bank Name',
        'branch': 'Branch', 'instagram': 'Instagram ID', 'followers': 'Followers',
        'following': 'Following', 'posts': 'Posts', 'bio': 'Bio',
        'ip': 'IP Address', 'location': 'Location', 'isp': 'ISP',
        'organization': 'Organization', 'asn': 'ASN'
    }

    all_data = []

    def extract_data(data, parent_key=""):
        if isinstance(data, dict):
            for key, value in data.items():
                if key in SKIP_KEYS:
                    continue
                display_key = DISPLAY_NAMES.get(key, key.replace('_', ' ').title())
                if parent_key:
                    display_key = f"{parent_key} {display_key}"
                if isinstance(value, dict):
                    extract_data(value, display_key)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            extract_data(item, display_key)
                        elif item and str(item).strip() and str(item).lower() not in ['none', 'null', '', 'n/a', 'na']:
                            all_data.append((display_key, str(item)))
                else:
                    if value and str(value).strip() and str(value).lower() not in ['none', 'null', '', 'n/a', 'na']:
                        all_data.append((display_key, str(value)))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    extract_data(item, f"Record {idx + 1}")
                elif item and str(item).strip() and str(item).lower() not in ['none', 'null', '', 'n/a', 'na']:
                    all_data.append((f"Item {idx + 1}", str(item)))

    extract_data(result)
    seen = set()
    unique_data = []
    for key, value in all_data:
        if key not in seen:
            seen.add(key)
            unique_data.append((key, value))

    if unique_data:
        formatted = ""
        for key, value in unique_data:
            emoji = get_emoji_for_key(key)
            formatted += f"{emoji} {key}: {value}\n"
    else:
        formatted = "📋 No detailed data available"

    msg = f"""
<blockquote>{title}</blockquote>

<blockquote>Query: {query}
{formatted}</blockquote>

💰 Credits Left: {credits_left}
"""
    return msg

def format_number(n):
    try:
        n = int(n)
        if n >= 1000000:
            return f"{n/1000000:.1f}M"
        elif n >= 1000:
            return f"{n/1000:.1f}K"
        return str(n)
    except:
        return str(n)

def format_rc_result(result, query, credits_left):
    e = NUM_EMOJIS
    divider = build_num_divider()

    if isinstance(result, dict) and result.get('status') == 'error':
        lines = []
        lines.append(divider)
        lines.append(te(e['phone_title'], '📞') + "  <b>𝗥𝗖 𝗗𝗘𝗧𝗔𝗜𝗟𝗦</b>  " + te(e['phone_title'], '📞'))
        lines.append(divider)
        lines.append("")
        lines.append("<blockquote>")
        lines.append(te(e['query'], '🔭') + " <b>Qᴜᴇʀʏ</b>  : <code>" + str(query) + "</code>")
        lines.append(te(e['status_ok'], '❌') + " " + str(result.get('message', 'NO DATA FOUND')))
        lines.append("</blockquote>")
        lines.append("")
        lines.append(divider)
        lines.append(te(e['credits'], '🧱') + " <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: " + str(credits_left))
        lines.append(divider)
        return [chr(10).join(lines)]

    if result.get('success') == True and result.get('vehicle_data'):
        vd = result.get('vehicle_data', {})
        rto = vd.get('rtoData', {})

        lines1 = []
        lines1.append(divider)
        lines1.append(te(e['phone_title'], '📞') + "  <b>𝗥𝗖 𝗗𝗘𝗧𝗔𝗜𝗟𝗦</b>  " + te(e['phone_title'], '📞'))
        lines1.append(divider)
        lines1.append("")
        lines1.append("<blockquote>")
        lines1.append(te(e['number'], '📲') + " <b>Vᴇʜɪᴄʟᴇ</b>    : <code>" + str(result.get('vehicle_number', query)) + "</code>")
        lines1.append(te(e['id_card'], '💳') + " <b>Eɴɢɪɴᴇ</b>     : <code>" + str(result.get('engine_number', 'N/A')) + "</code>")
        lines1.append(te(e['id_card'], '💳') + " <b>Cʜᴀꜱꜱɪꜱ</b>    : <code>" + str(result.get('chassis_number', 'N/A')) + "</code>")
        lines1.append(te(e['alt_num'], '📞') + " <b>Mᴏʙɪʟᴇ</b>     : <code>" + str(result.get('mobile_number', 'N/A')) + "</code>")
        lines1.append("</blockquote>")
        lines1.append("")
        lines1.append("<blockquote>")
        lines1.append(te(e['name'], '👤') + " <b>Oᴡɴᴇʀ</b>      : " + str(vd.get('owner', 'N/A')))
        lines1.append(te(e['father'], '👥') + " <b>Fᴀᴛʜᴇʀ</b>     : " + str(vd.get('ownerFatherName', 'N/A')))
        lines1.append(te(e['address'], '🏡') + " <b>Aᴅᴅʀᴇꜱꜱ</b>   : " + str(vd.get('presentAddress', 'N/A')))
        lines1.append(te(e['circle'], '🔎') + " <b>Pɪɴᴄᴏᴅᴇ</b>    : " + str(vd.get('pincode', 'N/A')))
        lines1.append("</blockquote>")
        lines1.append("")
        lines1.append("<blockquote>")
        lines1.append(te(e['name'], '🚗') + " <b>Vᴇʜɪᴄʟᴇ</b>    : " + str(vd.get('vehicle', 'N/A')))
        lines1.append(te(e['name'], '🏭') + " <b>Mᴀɴᴜꜰᴀᴄᴛᴜʀᴇʀ</b> : " + str(vd.get('manufacturer', 'N/A')))
        lines1.append(te(e['name'], '⚙️') + " <b>Vᴀʀɪᴀɴᴛ</b>    : " + str(vd.get('variant', 'N/A')))
        lines1.append(te(e['name'], '⛽') + " <b>Fᴜᴇʟ</b>       : " + str(vd.get('fuelType', 'N/A')))
        lines1.append(te(e['name'], '📅') + " <b>Rᴇɢ Dᴀᴛᴇ</b>   : " + str(vd.get('regDate', 'N/A')))
        lines1.append(te(e['name'], '📅') + " <b>Mꜰɢ Yᴇᴀʀ</b>   : " + str(vd.get('manufacturerYear', 'N/A')))
        lines1.append("</blockquote>")
        lines1.append(divider)

        lines2 = []
        lines2.append(divider)
        lines2.append(te(e['phone_title'], '📞') + "  <b>𝗥𝗖 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 (𝗖𝗼𝗻𝘁𝗶𝗻𝘂𝗲𝗱)</b>  " + te(e['phone_title'], '📞'))
        lines2.append(divider)
        lines2.append("")
        lines2.append("<blockquote>")
        lines2.append(te(e['name'], '🏛️') + " <b>RTO</b>        : " + str(rto.get('rtoName', 'N/A')))
        lines2.append(te(e['name'], '📍') + " <b>Sᴛᴀᴛᴇ</b>      : " + str(rto.get('statename', 'N/A')))
        lines2.append("</blockquote>")
        lines2.append("")
        lines2.append("<blockquote>")
        lines2.append(te(e['name'], '🏦') + " <b>Iɴꜱᴜʀᴀɴᴄᴇ</b>  : " + str(vd.get('insuranceCompanyName', 'N/A')))
        lines2.append(te(e['id_card'], '📋') + " <b>Pᴏʟɪᴄʏ</b>     : <code>" + str(vd.get('insurancePolicyNumber', 'N/A')) + "</code>")
        lines2.append(te(e['name'], '📅') + " <b>Vᴀʟɪᴅ Uᴘᴛᴏ</b> : " + str(vd.get('insuranceUpto', 'N/A')))
        lines2.append("</blockquote>")
        lines2.append("")
        lines2.append("<blockquote>")
        lines2.append(te(e['id_card'], '✅') + " <b>PUCC</b>       : <code>" + str(vd.get('puccNumber', 'N/A')) + "</code>")
        lines2.append(te(e['name'], '📅') + " <b>PUCC Vᴀʟɪᴅ</b> : " + str(vd.get('puccValidUpto', 'N/A')))
        lines2.append("</blockquote>")
        lines2.append("")
        lines2.append(divider)
        lines2.append(te(e['credits'], '🧱') + " <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: " + str(credits_left))
        lines2.append(divider)
        return [chr(10).join(lines1), chr(10).join(lines2)]

    return [format_api_result(result, "📋 RC DETAILS", query, credits_left)]

def auto_delete_post(chat_id, message_id, delay=120):
    def delete():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=delete, daemon=True).start()

def send_all_posts(chat_id, username, posts):
    if not posts:
        send_with_premium(chat_id, "❌ No posts found!")
        return

    info_text = f"📸 Sending {len(posts)} posts for @{username}... | ⏳ Please wait... | ⚠️ Posts will auto-delete in 2 minutes | ✅ Profile info will remain"
    info_msg = send_with_premium(chat_id, info_text)
    auto_delete_post(chat_id, info_msg.message_id, 30)

    for i, post in enumerate(posts, 1):
        image_url = post.get('img') or post.get('thumbnail')

        if image_url:
            caption = f"""
<b>📸 POST #{i}</b>

❤️ <b>Likes:</b> {format_number(post.get('likes', 0))}
💬 <b>Comments:</b> {format_number(post.get('comments', 0))}
📅 <b>Date:</b> {post.get('taken_at', 'Unknown')[:10] if post.get('taken_at') else 'Unknown'}

🔗 <a href="https://instagram.com/p/{post.get('code')}">View on Instagram</a>

⏰ <i>This post will auto-delete in 2 minutes</i>
"""
            try:
                cap = replace_with_premium_emojis(caption)
                sent_msg = bot.send_photo(chat_id, image_url, caption=cap, parse_mode='HTML')
                auto_delete_post(chat_id, sent_msg.message_id)
                time.sleep(0.5)
            except:
                post_text = f"🖼️ <a href='{image_url}'>Post #{i} - Click to view</a> | {caption}"
                sent_msg = send_with_premium(chat_id, post_text)
                auto_delete_post(chat_id, sent_msg.message_id)
                time.sleep(0.3)
        else:
            sent_msg = send_with_premium(chat_id, f"❌ Post #{i} - No image available")
            auto_delete_post(chat_id, sent_msg.message_id, 30)

    complete_text = f"✅ All {len(posts)} posts sent successfully for @{username}! | ⚠️ Posts will be deleted after 2 minutes | ✅ Profile info will remain in chat"
    complete_msg = send_with_premium(chat_id, complete_text)
    auto_delete_post(chat_id, complete_msg.message_id, 60)

def format_insta_result_v2(result, username, credits_left):
    e = NUM_EMOJIS
    divider = build_num_divider()

    if result.get('success') == False or result.get('status') == 'error':
        lines = []
        lines.append(divider)
        lines.append(te(e['phone_title'], '📞') + "  <b>𝗜𝗡𝗦𝗧𝗔𝗚𝗥𝗔𝗠 𝗢𝗦𝗜𝗡𝗧</b>  " + te(e['phone_title'], '📞'))
        lines.append(divider)
        lines.append("")
        lines.append("<blockquote>")
        lines.append(te(e['status_ok'], '❌') + " " + str(result.get('message', 'NO DATA FOUND')))
        lines.append("</blockquote>")
        lines.append("")
        lines.append(divider)
        lines.append(te(e['credits'], '🧱') + " <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: " + str(credits_left))
        lines.append(divider)
        return chr(10).join(lines), None, []

    profile = result.get('profile', {})
    recent_posts = result.get('recent_posts', [])
    osint_data = result.get('osint', {})

    if not profile and result.get('username'):
        profile = result
    if not recent_posts:
        recent_posts = result.get('posts', result.get('media', []))
    if not osint_data:
        osint_data = result.get('osint_data', result.get('records', {}))

    username_display = profile.get('username') or username
    full_name = profile.get('name') or 'N/A'
    user_id_insta = profile.get('id') or 'N/A'
    bio = profile.get('bio') or 'No bio'
    followers = profile.get('followers') or 0
    following = profile.get('following') or 0
    posts_count = profile.get('posts') or 0
    is_verified = '✅' if profile.get('verified') else '❌'
    is_private = '🔒' if profile.get('private') else '🌍'
    profile_pic = profile.get('pic') or ''
    external_url = profile.get('external_url', '')
    business = '✅' if profile.get('is_business', False) else '❌'
    category = profile.get('category_name', 'N/A')

    lines = []
    lines.append(divider)
    lines.append(te(e['phone_title'], '📞') + "  <b>𝗜𝗡𝗦𝗧𝗔𝗚𝗥𝗔𝗠 𝗢𝗦𝗜𝗡𝗧</b>  " + te(e['phone_title'], '📞'))
    lines.append(divider)
    lines.append("")
    lines.append("<blockquote>")
    lines.append(te(e['name'], '👤') + " <b>Uꜱᴇʀɴᴀᴍᴇ</b>  : @" + str(username_display))
    lines.append(te(e['name'], '📛') + " <b>Nᴀᴍᴇ</b>      : " + str(full_name if full_name else 'Not provided'))
    lines.append(te(e['id_card'], '🆔') + " <b>ID</b>        : " + str(user_id_insta))
    lines.append(te(e['status_ok'], '📝') + " <b>Bɪᴏ</b>       : " + str(bio[:300] if bio else 'No bio'))
    lines.append("")
    lines.append(te(e['records'], '📊') + " <b>𝗦𝗧𝗔𝗧𝗦</b>")
    lines.append(te(e['name'], '👥') + " <b>Fᴏʟʟᴏᴡᴇʀꜱ</b> : " + str(format_number(followers)))
    lines.append(te(e['name'], '➡️') + " <b>Fᴏʟʟᴏᴡɪɴɢ</b> : " + str(format_number(following)))
    lines.append(te(e['name'], '🖼️') + " <b>Pᴏꜱᴛꜱ</b>     : " + str(format_number(posts_count)))
    lines.append(te(e['status_ok'], '✅') + " <b>Vᴇʀɪꜰɪᴇᴅ</b>  : " + str(is_verified))
    lines.append(te(e['status_ok'], '🔒') + " <b>Pʀɪᴠᴀᴛᴇ</b>   : " + str(is_private))
    lines.append(te(e['name'], '🏢') + " <b>Bᴜꜱɪɴᴇꜱꜱ</b>  : " + str(business))
    lines.append(te(e['name'], '📂') + " <b>Cᴀᴛᴇɢᴏʀʏ</b>  : " + str(category))
    lines.append("</blockquote>")

    if external_url:
        lines.append("")
        lines.append("<blockquote>" + te(e['status_ok'], '🔗') + " <b>Exᴛᴇʀɴᴀʟ URL</b>: " + str(external_url) + "</blockquote>")

    if osint_data.get('available') and osint_data.get('records'):
        records = osint_data.get('records', [])
        lines.append("")
        lines.append("<blockquote>" + te(e['status_ok'], '🔍') + " <b>𝗢𝗦𝗜𝗡𝗧 𝗥𝗘𝗖𝗢𝗥𝗗𝗦</b> (" + str(len(records)) + " found)</blockquote>")
        for idx_rec, record in enumerate(records, 1):
            lines.append("")
            lines.append("<blockquote>" + te(e['record_badge'], '📰') + " <b>Rᴇᴄᴏʀᴅ #" + str(idx_rec) + "</b>")
            if record.get('name'): lines.append("   " + te(e['name'], '👤') + " <b>Nᴀᴍᴇ</b>: " + str(record.get('name')))
            if record.get('email'): lines.append("   " + te(e['email'], '📧') + " <b>Eᴍᴀɪʟ</b>: " + str(record.get('email')))
            if record.get('phone'): lines.append("   " + te(e['number'], '📲') + " <b>Pʜᴏɴᴇ</b>: " + str(record.get('phone')))
            if record.get('address'): lines.append("   " + te(e['address'], '🏡') + " <b>Aᴅᴅʀᴇꜱꜱ</b>: " + str(record.get('address')[:200]))
            if record.get('city'): lines.append("   " + te(e['circle'], '🏙️') + " <b>Cɪᴛʏ</b>: " + str(record.get('city')))
            if record.get('state'): lines.append("   " + te(e['circle'], '🗺️') + " <b>Sᴛᴀᴛᴇ</b>: " + str(record.get('state')))
            if record.get('dob'): lines.append("   " + te(e['name'], '🎂') + " <b>DOB</b>: " + str(record.get('dob')))
            if record.get('aadhar'): lines.append("   " + te(e['id_card'], '🆔') + " <b>Aᴀᴅʜᴀʀ</b>: " + str(record.get('aadhar')))
            if record.get('pan'): lines.append("   " + te(e['id_card'], '📄') + " <b>PAN</b>: " + str(record.get('pan')))
            lines.append("</blockquote>")
        lines.append("")
    else:
        lines.append("")
        lines.append("<blockquote>" + te(e['status_ok'], '🔍') + " <b>𝗢𝗦𝗜𝗡𝗧 𝗥𝗘𝗖𝗢𝗥𝗗𝗦</b></blockquote>")
        lines.append("")
        lines.append(te(e['status_ok'], '❌') + " OSINT data not available")
        lines.append("")

    if recent_posts:
        lines.append("")
        lines.append("<blockquote>" + te(e['phone_title'], '📸') + " <b>𝗥𝗘𝗖𝗘𝗡𝗧 𝗣𝗢𝗦𝗧𝗦</b></blockquote>")
        lines.append("")
        lines.append(te(e['records'], '📊') + " <b>Tᴏᴛᴀʟ</b>: " + str(len(recent_posts)) + " posts")
        for idx_post, post in enumerate(recent_posts[:10], 1):
            likes = post.get('likes', post.get('like_count', 0))
            comments = post.get('comments', post.get('comment_count', 0))
            caption_text = post.get('caption', post.get('text', ''))[:50]
            post_line = "   " + te(e['phone_title'], '🖼️') + " <b>Pᴏꜱᴛ #" + str(idx_post) + "</b>: " + te(e['name'], '❤️') + str(format_number(likes)) + " " + te(e['name'], '💬') + str(format_number(comments))
            if caption_text: post_line += " - " + caption_text + "..."
            lines.append(post_line)
        if len(recent_posts) > 10:
            lines.append("   ... and " + str(len(recent_posts) - 10) + " more posts")
        lines.append(te(e['status_ok'], '💡') + " Click VIEW ALL POSTS button below!")
        lines.append("")
    else:
        lines.append("")
        lines.append("<blockquote>" + te(e['phone_title'], '📸') + " <b>𝗥𝗘𝗖𝗘𝗡𝗧 𝗣𝗢𝗦𝗧𝗦</b></blockquote>")
        lines.append("")
        lines.append(te(e['status_ok'], '❌') + " No recent posts found")
        lines.append("")

    lines.append(divider)
    lines.append(te(e['credits'], '🧱') + " <b>Cʀᴇᴅɪᴛꜱ Lᴇꜰᴛ</b>: " + str(credits_left))
    lines.append(divider)

    return chr(10).join(lines), profile_pic, recent_posts

@bot.message_handler(commands=['tgid'])
def tgid_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(chat_id, """❌ Use: /tgid [username or user_id]

📝 Examples:
/tgid BMW_AURA1
/tgid @TATANIUM_ANSH
/tgid 8695946179

🔍 Get Telegram user phone info via username OR user ID
""")
        return

    query = parts[1].strip().replace('@', '')
    if 't.me/' in query:
        query = query.split('t.me/')[-1]

    if not query:
        send_with_premium(chat_id, "❌ Invalid username!")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(chat_id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    working, status_msg = check_api_status('tgid')
    if not working:
        send_with_premium(chat_id, f"""
<blockquote>🔍 TELEGRAM USER INFO</blockquote>

<blockquote>⚠️ API IS UNDER MAINTENANCE/FIXING
{status_msg or 'Please try again later'}</blockquote>
""")
        return

    try:
        bot.send_chat_action(chat_id, 'typing')
    except:
        pass

    wait = send_with_premium(chat_id, f"🔍 Fetching Telegram info for @{query}...")
    result = call_tg_api(query)

    formatted_msg = format_tgid_result(result, query, credits_left)
    json_file = save_result_to_json("tgid", query, result)

    if json_file:
        sent_msg = send_result_with_json(chat_id, formatted_msg, json_file, wait.message_id)
    else:
        sent_msg = send_result(chat_id, formatted_msg, wait)

    if sent_msg:
        send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['num'])
def num_cmd(message):
    if not is_recent_command(message):
        return

    user_id  = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(chat_id,
            "❌ Use: /num [phone_number]\n\n"
            "📝 Examples:\n/num 9876543210\n/num +919876543210\n\n"
            "🔍 Get detailed information about any Indian phone number"
        )
        return

    phone = re.sub(r'[^\d+]', '', parts[1].strip())

    if not validate_phone(phone):
        send_with_premium(chat_id, "❌ Invalid phone number! Use 10-15 digits with optional +")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(chat_id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    working, status_msg = check_api_status('num')
    if not working:
        send_with_premium(chat_id, f"<blockquote>📱 PHONE NUMBER INFO</blockquote>\n\n"
                                    f"<blockquote>⚠️ API IS UNDER MAINTENANCE\n{status_msg or 'Try later'}</blockquote>")
        return

    try:
        bot.send_chat_action(chat_id, 'typing')
    except Exception:
        pass

    wait   = send_with_premium(chat_id, f"🔍 Fetching info for {phone}...")
    result = call_phone_api(phone)

    pages     = format_number_result(result, phone, credits_left)
    json_file = save_result_to_json("num", phone, result)

    NUM_PAGINATION[user_id] = {"pages": pages, "json_file": json_file, "query": phone}

    first_txt, first_markup = pages[0]

    if len(pages) == 1 and json_file:
        if first_markup is None:
            first_markup = InlineKeyboardMarkup()
        file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
        JSON_FILES[file_id] = json_file
        first_markup.add(InlineKeyboardButton("Download JSON", callback_data=f"dljson_{file_id}"))

    try:
        bot.delete_message(chat_id, wait.message_id)
    except Exception:
        pass

    sent_msg = send_with_premium(chat_id, first_txt, reply_markup=first_markup)
    if sent_msg:
        schedule_deletion(sent_msg.message_id, chat_id)
        send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['adhr'])
def adhr_cmd(message):
    if not is_recent_command(message):
        return

    user_id   = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id,
            "❌ Use: /adhr [AADHAR_NUMBER]\n\n"
            "📝 Examples:\n/adhr 942660008471\n/adhr 393933081942\n\n"
            "🔍 Get detailed Aadhar linked information"
        )
        return

    aadhar = re.sub(r'[^\d]', '', parts[1].strip())

    if not validate_aadhar(aadhar):
        send_with_premium(message.chat.id, "❌ Invalid Aadhar number! Use 12 digits only!")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(message.chat.id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    working, status_msg = check_api_status('adhr')
    if not working:
        send_with_premium(message.chat.id,
            f"<blockquote>🪪 AADHAR INFO</blockquote>\n\n"
            f"<blockquote>⚠️ API IS UNDER MAINTENANCE\n{status_msg or 'Please try again later'}</blockquote>"
        )
        return

    try:
        bot.send_chat_action(chat_id, 'typing')
    except Exception:
        pass

    wait      = send_with_premium(chat_id, f"🔍 Fetching Aadhar info for {aadhar}...")
    result    = call_aadhar_api(aadhar)
    json_file = save_result_to_json("adhr", aadhar, result)
    pages     = format_aadhar_result(result, aadhar, credits_left)

    # store in NUM_PAGINATION so the existing num_page_ callback handles navigation
    NUM_PAGINATION[user_id] = {"pages": pages, "json_file": json_file, "query": aadhar}

    first_txt, first_markup = pages[0]

    if len(pages) == 1 and json_file:
        if first_markup is None:
            first_markup = InlineKeyboardMarkup()
        file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
        JSON_FILES[file_id] = json_file
        first_markup.add(InlineKeyboardButton("Download JSON", callback_data=f"dljson_{file_id}"))

    try:
        bot.delete_message(chat_id, wait.message_id)
    except Exception:
        pass

    sent_msg = send_with_premium(chat_id, first_txt, reply_markup=first_markup)
    if sent_msg:
        schedule_deletion(sent_msg.message_id, chat_id)
        send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['tguser'])
def tguser_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id, """❌ Use: /tguser [username]

📝 Examples:
/tguser BMW_AURA1
/tguser @TATANIUM_ANSH

💡 Get any Telegram user's ID
""")
        return

    username = parts[1].strip()
    username = username.replace('@', '')
    if 't.me/' in username:
        username = username.split('t.me/')[-1]

    if not username:
        send_with_premium(message.chat.id, "❌ Invalid username!")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(message.chat.id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    bot.send_chat_action(chat_id, 'typing')
    wait = send_with_premium(chat_id, f"🔍 Fetching Telegram user ID for @{username}...")

    try:
        chat = bot.get_chat(f"@{username}")
        target_user_id = chat.id

        msg = f"""
<blockquote>👤 TELEGRAM USER INFO</blockquote>

<blockquote>🔍 Username: @{username}
🆔 User ID: <code>{target_user_id}</code>
📝 First Name: {chat.first_name or 'N/A'}
📛 Last Name: {chat.last_name or 'N/A'}
👑 Is Bot: {'Yes' if chat.is_bot else 'No'}
📌 Chat Type: {chat.type}</blockquote>

💰 Credits Left: {credits_left}
"""
        json_data = {
            "username": username,
            "user_id": target_user_id,
            "first_name": chat.first_name,
            "last_name": chat.last_name,
            "is_bot": chat.is_bot,
            "chat_type": chat.type
        }
        json_file = save_result_to_json("tguser", username, json_data)

        if json_file:
            sent_msg = send_result_with_json(chat_id, msg, json_file, wait.message_id)
        else:
            sent_msg = send_result(chat_id, msg, wait)

        if sent_msg:
            send_random_media(chat_id, sent_msg.message_id)

    except Exception as e:
        error_msg_text = str(e)
        if "user not found" in error_msg_text.lower():
            error_msg_text = "User not found! Make sure the username exists."

        msg = f"""
<blockquote>👤 TELEGRAM USER INFO</blockquote>

<blockquote>🔍 Username: @{username}
❌ {error_msg_text}</blockquote>

💰 Credits Left: {credits_left}
"""
        sent_msg = send_result(chat_id, msg, wait)
        if sent_msg:
            send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return

    username = message.from_user.username or "N/A"
    first_name = message.from_user.first_name or "User"
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    referred = extract_referral(message.text)
    if not get_user(user_id):
        create_user(user_id, username, first_name, referred)
    credits = get_credits(user_id)

    bot_username = bot.get_me().username

    msg = f"""<blockquote>
🌟 WELCOME TO RAJPUT OSINT BOT🌟

👋 Hello {first_name}!
🆔 ID: <code>{user_id}</code>
💰 Credits: {credits}

🔍 OSINT COMMANDS:
📱 /num 9876543210 - Indian Phone
👤 /tgid username - Telegram info (Phone lookup)
📱 /num2 9876543210 - Phone number info (Alternate API)
👤 /name abhiraaj - Name to details
📄 /pan AXDPR2606K - PAN Card info
🆔 /adhr 393933081942 - Aadhar info
🚗 /vech HR26DA1337 - Vehicle info
📋 /vechrc HR26EV0001 - RC info
💳 /upi id@bank - UPI ID info
🏦 /ifsc SBIN0001234 - Bank info
🌐 /ip 8.8.8.8 - IP info
📮 /pin 110001 - Pincode info
🐙 /git username - GitHub info
🎮 /bgmi 5121439477 - BGMI info
🔥 /ff 123456789 - FreeFire info
📸 /insta username - Instagram info
👨‍👩‍👧‍👦 /family 9876543210 - Family Details
🎨 /ai prompt - AI Image Generation

🎫 OTHER COMMANDS:
/redeem CODE - Redeem credits
/profile - Your profile
/balance - Check credits
/refer - Referral link
/help - All commands</blockquote>

👑 Owner: {OWNER_USERNAME}
"""

    if is_admin(user_id):
        msg += f"""

👑 ADMIN COMMANDS

/admin - Open Admin Panel
/gen [credits] [uses] [days] - Create code
/deletecode [code] - Delete redeem code
/add [id] [credits] - Add credits
/removecredit [id] [credits] - Remove credits
/promote [id] - Make admin
/demote [id] - Remove admin
/users - List users
/stats - Bot stats
/allcodes - All redeem codes
/broadcast [msg] - Send to all users
/uptime - Bot uptime
/searchuser [id/username] - Search user
/block [id] - Block user
/unblock [id] - Unblock user
/lock - Lock bot
/unlock - Unlock bot
/commands - Command usage stats
/addc [url] - Add force join channel
/removec [url/@username] - Remove channel
/listc - List all channels
/api - List all API endpoints
/apic [command] [api_url] - Change API endpoint
/apistatus [command] [working/fixing] [message] - Set API status
/newapi - Create custom API command
/lockf - Disable force join
/unlockf - Enable force join

[ MEDIA GALLERY ADMIN ]
/addvideo - Add videos in bulk
/addphoto - Add photos in bulk
/delvideo - Delete video
/delphoto - Delete photo
/listvideos - List all videos
/listphotos - List all photos
/setmode [video/photo/both] - Set media mode
"""

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        create_primary_button("❓ Help", callback_data="help"),
        create_primary_button("👤 Profile", callback_data="profile"),
        create_primary_button("💰 Balance", callback_data="balance"),
        create_success_button("🎫 Redeem", callback_data="redeem"),
    )
    markup.add(create_success_button("➕ ADD BOT TO GROUP", url=f"https://t.me/+UemRGWr-B2wzMmFl{bot_username}?startgroup=start"))

    if is_admin(user_id):
        markup.add(create_danger_button("👑 Admin Panel", callback_data="admin_panel"))

    try:
        sent = send_with_premium(chat_id, msg, parse_mode='HTML', reply_markup=markup)
        schedule_deletion(sent.message_id, chat_id)
    except Exception as e:
        print(f"Error in start command: {e}")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    credits = get_credits(user_id)
    bot_username = bot.get_me().username

    msg = f"""<blockquote>
📚 COMPLETE HELP MENU

🔍 OSINT COMMANDS:
📱 /num 9876543210 - Indian number
👤 /tgid username - Telegram info (Phone lookup)
📱 /num2 9876543210 - Phone number info (Alternate API)
👤 /name abhiraaj - Name to details
📄 /pan AXDPR2606K - PAN Card info
🆔 /adhr 393933081942 - Aadhar info
🚗 /vech HR26DA1337 - Vehicle info
📋 /vechrc HR26EV0001 - RC info
💳 /upi id@bank - UPI ID info
🏦 /ifsc SBIN0001234 - Bank info
🌐 /ip 8.8.8.8 - IP info
🔍 /osint [query] - Universal OSINT search
📮 /pin 110001 - Pincode info
🐙 /git username - GitHub info
🎮 /bgmi 5121439477 - BGMI info
🔥 /ff 123456789 - FreeFire info
📸 /insta username - Instagram info
👨‍👩‍👧‍👦 /family 9876543210 - Family Details
🎨 /ai prompt - Generate AI images

🎫 ACCOUNT COMMANDS:
/redeem CODE - Redeem credits
/profile - Your profile
/balance - Check credits
/refer - Get referral link</blockquote>

💰 Your Credits: {credits}

[ MEDIA GALLERY ]
🎬 After every command result, random videos/photos will appear!
👑 Admin can add multiple videos/photos at once using /addvideo or /addphoto
"""
    markup = InlineKeyboardMarkup()
    markup.add(create_success_button("➕ ADD BOT TO GROUP", url=f"https://t.me/+UemRGWr-B2wzMmFl{bot_username}?startgroup=start"))

    try:
        sent = send_with_premium(chat_id, msg, parse_mode='HTML', reply_markup=markup)
        schedule_deletion(sent.message_id, chat_id)
    except Exception as e:
        print(f"Error in help command: {e}")

@bot.message_handler(commands=['profile'])
def profile_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    user_data = get_user(user_id)
    if not user_data:
        send_with_premium(chat_id, "❌ Please /start first!")
        return
    msg = f"""
👤 YOUR PROFILE

🆔 ID: <code>{user_data[0]}</code>
👤 Username: @{user_data[1] or 'N/A'}
📝 Name: {user_data[2] or 'User'}
💰 Credits: {user_data[3] or 0}
👥 Referrals: {user_data[6] or 0}
⚡ Commands Used: {user_data[9] or 0}
👑 Admin: {'✅' if user_data[4] == 1 or user_id == ADMIN_ID else '❌'}
📅 Joined: {str(user_data[7])[:10] if user_data[7] else 'N/A'}
"""
    try:
        sent = send_with_premium(chat_id, msg, parse_mode='HTML')
        schedule_deletion(sent.message_id, chat_id)
    except Exception as e:
        print(f"Error in profile command: {e}")

@bot.message_handler(commands=['balance'])
def balance_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    credits = get_credits(user_id)
    msg = f"""
💰 CREDIT BALANCE

💳 Credits: {credits}
"""
    try:
        sent = send_with_premium(chat_id, msg)
        schedule_deletion(sent.message_id, chat_id)
    except Exception as e:
        print(f"Error in balance command: {e}")

@bot.message_handler(commands=['refer'])
def refer_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    bot_user = bot.get_me().username
    link = f"https://t.me/+UemRGWr-B2wzMmFl{bot_user}?start=ref_{user_id}"
    msg = f"""
🔗 YOUR REFERRAL LINK

📨 <code>{link}</code>

📋 Rules:
• Friend gets: {REFERRAL_BONUS_NEW} credits
• You gets: {REFERRAL_BONUS_REFERRER} credits
"""
    try:
        sent = send_with_premium(chat_id, msg, parse_mode='HTML')
        schedule_deletion(sent.message_id, chat_id)
    except Exception as e:
        print(f"Error in refer command: {e}")

@bot.message_handler(commands=['redeem'])
def redeem_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split()
    if len(parts) < 2:
        msg = """❌ USE: /redeem CODE

💡 EXAMPLE: /redeem ABC123XYZ

⚠️ NOTE: Each code can be used only ONCE per user!

🎫 Get codes from admin: @sahilxalone"""
        send_with_premium(chat_id, msg)
        return

    code = parts[1].strip().upper()
    wait_msg = send_with_premium(chat_id, f"🔍 Verifying code: {code}...")
    success, result = redeem_credits(user_id, code)

    if success:
        new_credits = get_credits(user_id)
        match = re.search(r'(\d+)', result)
        amount = match.group(1) if match else "10"

        final_msg = f"""✅ REDEMPTION SUCCESSFUL! ✅

🎫 Code: {code}
💰 Credits Added: +{amount}
💳 New Balance: {new_credits} credits

✨ Use /balance to check your credits
✨ Use /profile to see your stats"""

        try:
            edit_with_premium(chat_id, wait_msg.message_id, final_msg)
        except:
            bot.delete_message(chat_id, wait_msg.message_id)
            send_with_premium(chat_id, final_msg)
    else:
        final_msg = f"""❌ REDEMPTION FAILED ❌

🎫 Code: {code}
❌ Error: {result}

💡 Possible reasons:
• Invalid or expired code
• Code already used by you
• Code max usage reached
• Code doesn't exist

📞 Contact admin: {OWNER_USERNAME}"""

        try:
            edit_with_premium(chat_id, wait_msg.message_id, final_msg)
        except:
            bot.delete_message(chat_id, wait_msg.message_id)
            send_with_premium(chat_id, final_msg)

def handle_api_command(message, command_name, api_func, validate_func, title, query_processor=None):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(chat_id, f"❌ Use: /{command_name} [query]")
        return

    query = parts[1].strip()
    if query_processor:
        query = query_processor(query)
    if validate_func and not validate_func(query):
        send_with_premium(chat_id, f"❌ Invalid {command_name} format!")
        return

    working, status_msg = check_api_status(command_name)
    if not working:
        send_with_premium(chat_id, f"""
<blockquote>{title}</blockquote>

<blockquote>⚠️ API IS UNDER MAINTENANCE/FIXING
{status_msg or 'Please try again later'}</blockquote>
""")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(chat_id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    try:
        bot.send_chat_action(chat_id, 'typing')
    except:
        pass

    wait = send_with_premium(chat_id, f"🔍 Fetching {title}...")
    result = api_func(query)

    formatted_msg = format_api_result(result, title, query, credits_left)
    json_file = save_result_to_json(command_name, query, result)

    if json_file:
        sent_msg = send_result_with_json(chat_id, formatted_msg, json_file, wait.message_id)
    else:
        sent_msg = send_result(chat_id, formatted_msg, wait)

    if sent_msg:
        send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['name'])
def name_cmd(message):
    handle_api_command(message, 'name', call_name_api, None, "👤 NAME SEARCH")

@bot.message_handler(commands=['pan'])
def pan_cmd(message):
    handle_api_command(message, 'pan', call_pan_api, validate_pan, "📄 PAN CARD INFO", lambda x: x.upper())

@bot.message_handler(commands=['vech'])
def vech_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(chat_id,
            "❌ Use: /vech [VEHICLE_NUMBER]\n\n"
            "📝 Examples:\n/vech MH12AB1234\n/vech DL01AB1234\n\n"
            "🔍 Get detailed vehicle information"
        )
        return

    vehicle = parts[1].strip().upper().replace(' ', '')
    if not validate_vehicle(vehicle):
        send_with_premium(chat_id, "❌ Invalid vehicle number format!")
        return

    working, status_msg = check_api_status('vech')
    if not working:
        send_with_premium(chat_id, f"""
<blockquote>🚗 VEHICLE INFO</blockquote>

<blockquote>⚠️ API IS UNDER MAINTENANCE/FIXING
{status_msg or 'Please try again later'}</blockquote>
""")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(chat_id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    try:
        bot.send_chat_action(chat_id, 'typing')
    except:
        pass

    wait = send_with_premium(chat_id, f"🔍 Fetching vehicle info for {vehicle}...")
    result = call_vehicle_api(vehicle)

    pages = format_vehicle_result_v2(result, vehicle, credits_left)
    json_file = save_result_to_json("vech", vehicle, result)

    if len(pages) == 1:
        # Single page - send directly with JSON button
        markup = InlineKeyboardMarkup()
        if json_file:
            file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
            JSON_FILES[file_id] = json_file
            markup.add(InlineKeyboardButton("📥 Download JSON", callback_data=f"dljson_{file_id}"))
        markup.add(create_default_button("🔙 Back", callback_data="back_to_result"))
        try:
            bot.delete_message(chat_id, wait.message_id)
        except:
            pass
        sent = send_with_premium(chat_id, pages[0], reply_markup=markup)
        if sent:
            schedule_deletion(sent.message_id, chat_id)
            send_random_media(chat_id, sent.message_id)
    else:
        # Multi-page with pagination
        send_paginated_vech(chat_id, user_id, pages, json_file, vehicle, wait, command="vech")


@bot.message_handler(commands=['vechrc'])
def vechrc_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(chat_id,
            "❌ Use: /vechrc [VEHICLE_NUMBER]\n\n"
            "📝 Examples:\n/vechrc MH12AB1234\n/vechrc DL01AB1234\n\n"
            "🔍 Get detailed RC (Registration Certificate) information"
        )
        return

    vehicle = parts[1].strip().upper().replace(' ', '')
    if not validate_vehicle(vehicle):
        send_with_premium(chat_id, "❌ Invalid vehicle number format!")
        return

    working, status_msg = check_api_status('vechrc')
    if not working:
        send_with_premium(chat_id, f"""
<blockquote>📋 RC DETAILS</blockquote>

<blockquote>⚠️ API IS UNDER MAINTENANCE/FIXING
{status_msg or 'Please try again later'}</blockquote>
""")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(chat_id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    try:
        bot.send_chat_action(chat_id, 'typing')
    except:
        pass

    wait = send_with_premium(chat_id, f"🔍 Fetching RC details for {vehicle}...")
    result = call_rc_api(vehicle)

    pages = format_rc_result_v2(result, vehicle, credits_left)
    json_file = save_result_to_json("vechrc", vehicle, result)

    if len(pages) == 1:
        markup = InlineKeyboardMarkup()
        if json_file:
            file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
            JSON_FILES[file_id] = json_file
            markup.add(InlineKeyboardButton("📥 Download JSON", callback_data=f"dljson_{file_id}"))
        markup.add(create_default_button("🔙 Back", callback_data="back_to_result"))
        try:
            bot.delete_message(chat_id, wait.message_id)
        except:
            pass
        sent = send_with_premium(chat_id, pages[0], reply_markup=markup)
        if sent:
            schedule_deletion(sent.message_id, chat_id)
            send_random_media(chat_id, sent.message_id)
    else:
        send_paginated_vech(chat_id, user_id, pages, json_file, vehicle, wait, command="vechrc")

@bot.message_handler(commands=['ip'])
def ip_cmd(message):
    handle_api_command(message, 'ip', call_ip_api, validate_ip, "🌐 IP ADDRESS INFO")

@bot.message_handler(commands=['pin'])
def pin_cmd(message):
    handle_api_command(message, 'pin', call_pincode_api, validate_pincode, "📮 PINCODE INFO")

@bot.message_handler(commands=['git'])
def git_cmd(message):
    handle_api_command(message, 'git', call_git_api, None, "🐙 GITHUB PROFILE", lambda x: x.replace('@', ''))

@bot.message_handler(commands=['bgmi'])
def bgmi_cmd(message):
    handle_api_command(message, 'bgmi', call_bgmi_api, None, "🎮 BGMI PLAYER INFO")

@bot.message_handler(commands=['ff'])
def ff_cmd(message):
    handle_api_command(message, 'ff', call_ff_api, None, "🔥 FREEFIRE PLAYER INFO")

@bot.message_handler(commands=['upi'])
def upi_cmd(message):
    handle_api_command(message, 'upi', call_upi_api, validate_upi, "💳 UPI ID INFO")

@bot.message_handler(commands=['ifsc'])
def ifsc_cmd(message):
    handle_api_command(message, 'ifsc', call_ifsc_api, validate_ifsc, "🏦 BANK INFO", lambda x: x.upper())

@bot.message_handler(commands=['family'])
def family_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id, """❌ Use: /family [AADHAR_NUMBER]

📝 Examples:
/family 377226634228

👨‍👩‍👧‍👦 Get family details linked to an Aadhar number
""")
        return

    phone = parts[1].strip()
    phone = re.sub(r'[^\d+]', '', phone)

    if not validate_phone(phone):
        send_with_premium(message.chat.id, "❌ Invalid phone number! Use 10-15 digits with optional +")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(message.chat.id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    working, status_msg = check_api_status('family')
    if not working:
        send_with_premium(message.chat.id, f"""
<blockquote>👨‍👩‍👧‍👦 FAMILY DETAILS</blockquote>

<blockquote>⚠️ API IS UNDER MAINTENANCE/FIXING
{status_msg or 'Please try again later'}</blockquote>
""")
        return

    bot.send_chat_action(chat_id, 'typing')
    wait = send_with_premium(message.chat.id, f"🔍 Fetching family details for Aadhar {phone}...")

    result = call_family_api(phone)
    formatted_msg = format_api_result(result, "👨‍👩‍👧‍👦 FAMILY DETAILS (Aadhar)", phone, credits_left)
    json_file = save_result_to_json("family", phone, result)

    if json_file:
        sent_msg = send_result_with_json(chat_id, formatted_msg, json_file, wait.message_id)
    else:
        sent_msg = send_result(chat_id, formatted_msg, wait)

    if sent_msg:
        send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['ai'])
def ai_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    working, status_msg = check_api_status('ai')
    if not working:
        send_with_premium(message.chat.id, f"""
<blockquote>🎨 AI IMAGE GENERATION</blockquote>

<blockquote>⚠️ API IS UNDER MAINTENANCE/FIXING
{status_msg or 'Please try again later'}</blockquote>
""")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id, """
🎨 AI IMAGE GENERATION

❌ Please provide a prompt!

📝 Usage: `/ai [prompt]`

<blockquote>✨ Examples:
/ai beautiful sunset over mountains
/ai cyberpunk city at night
/ai cute cat wearing sunglasses</blockquote>

⚡ Powered by Pollinations AI
""")
        return

    prompt = parts[1].strip()
    if len(prompt) < 3:
        send_with_premium(message.chat.id, "❌ Prompt too short! Please provide at least 3 characters.")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(message.chat.id, "❌ Insufficient credits! Get more via referral or redeem codes.")
            return

    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    bot.send_chat_action(chat_id, 'upload_photo')
    wait = send_searching_animation(chat_id)
    bot.send_chat_action(chat_id, 'upload_photo')

    seed = random.randint(1, 999999)
    encoded_prompt = requests.utils.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"

    try:
        img_response = requests.get(image_url, timeout=30, stream=True)
        if img_response.status_code == 200:
            content_type = img_response.headers.get('content-type', '')
            if 'image' in content_type:
                temp_file = f"temp_ai_{random.randint(10000, 99999)}.png"
                with open(temp_file, 'wb') as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                with open(temp_file, 'rb') as f:
                    cap_text = f"""
🎨 AI IMAGE GENERATION

🔍 Prompt: {prompt}

💰 Credits Left: {credits_left}
"""
                    caption = replace_with_premium_emojis(cap_text)
                    sent_msg = bot.send_photo(chat_id, f, caption=caption, parse_mode='HTML')
                    send_random_media(chat_id, sent_msg.message_id)
                os.remove(temp_file)
                bot.delete_message(chat_id, wait.message_id)
            else:
                raise Exception(f"Not an image, content-type: {content_type}")
        else:
            raise Exception(f"HTTP {img_response.status_code}")
    except Exception as e:
        msg = f"""
🎨 AI IMAGE GENERATION

🔍 Prompt: {prompt}
🖼️ Click to view: {image_url}

💰 Credits Left: {credits_left}

💡 The image was generated but couldn't be downloaded.
   Click the link above to view it!
"""
        sent_msg = send_result(chat_id, msg, wait)
        if sent_msg:
            send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['num2'])
def num2_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id, """❌ Use: /num2 [phone_number]

📝 Examples:
/num2 9876543210
/num2 +919876543210

🔍 Get detailed information about any phone number
""")
        return

    phone = parts[1].strip()
    phone = re.sub(r'[^\d+]', '', phone)

    if not validate_phone(phone):
        send_with_premium(message.chat.id, "❌ Invalid phone number! Use 10-15 digits with optional +")
        return

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(message.chat.id, "❌ Insufficient credits!")
            return
    credits_left = get_credits(user_id) if not is_group_chat(message) else "∞ (Group)"

    bot.send_chat_action(chat_id, 'typing')
    wait = send_with_premium(message.chat.id, f"🔍 Fetching info for {phone}...")

    result = call_num2_api(phone)
    formatted_msg = format_api_result(result, "📱 PHONE NUMBER INFO (Alt)", phone, credits_left)
    json_file = save_result_to_json("num2", phone, result)

    if json_file:
        sent_msg = send_result_with_json(chat_id, formatted_msg, json_file, wait.message_id)
    else:
        sent_msg = send_result(chat_id, formatted_msg, wait)

    if sent_msg:
        send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['insta'])
def insta_cmd(message):
    if not is_recent_command(message):
        return

    user_id = message.from_user.id
    error_msg = get_access_error_message(user_id)
    if error_msg:
        send_with_premium(message.chat.id, error_msg)
        return
    chat_id = message.chat.id

    if not enforce_force_join(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Use: /insta [username]\n\nExample: <code>/insta just_sahil_621</code>")
        return

    username = parts[1].strip().replace('@', '')

    if not is_group_chat(message):
        if not deduct_credit(user_id):
            send_with_premium(message.chat.id, "❌ Insufficient credits!")
            return
        credits_left = get_credits(user_id)
    else:
        credits_left = "∞ (Group)"

    try:
        bot.send_chat_action(chat_id, 'typing')
    except:
        pass

    wait = send_with_premium(chat_id, f"🔍 Fetching Instagram profile for @{username}...")
    result = call_insta_api(username)

    if result.get('status') == 'error':
        msg = f"""
<blockquote>📸 INSTAGRAM OSINT</blockquote>

<blockquote>❌ Instagram API is currently down. Please try again later.</blockquote>

💰 Credits Left: {credits_left}
"""
        sent_msg = send_result(chat_id, msg, wait)
        if sent_msg:
            send_random_media(chat_id, sent_msg.message_id)
        return

    profile = result.get('profile', {})
    osint_data = result.get('osint', {})
    is_private = profile.get('private', False)

    recent_posts = []
    if not is_private:
        recent_posts = profile.get('recent_posts', [])
        if not recent_posts:
            recent_posts = result.get('recent_posts', [])
        if not recent_posts:
            recent_posts = profile.get('posts', [])
        if not recent_posts:
            recent_posts = result.get('posts', [])

    if is_private:
        username_display = profile.get('username') or username
        full_name = profile.get('name') or 'N/A'
        user_id_insta = profile.get('id') or 'N/A'
        bio = profile.get('bio') or 'No bio'
        followers = profile.get('followers') or 0
        following = profile.get('following') or 0
        posts_count = profile.get('posts') or 0
        is_verified = '✅' if profile.get('verified') else '❌'
        profile_pic = profile.get('pic') or ''

        msg = f"""
<blockquote>📸 INSTAGRAM OSINT</blockquote>

<blockquote>👤 Username  : @{username_display}
📛 Name      : {full_name if full_name else 'Not provided'}
🆔 ID        : {user_id_insta}
📝 Bio       : {bio[:150] if bio else 'No bio'}

📊 STATS
👥 Followers : {format_number(followers)}
➡️ Following : {format_number(following)}
🖼️ Posts     : {format_number(posts_count)}
✅ Verified  : {is_verified}
🔒 PRIVATE   : YES - Account is private</blockquote>

<blockquote>🔍 OSINT RECORDS</blockquote>
"""
        if osint_data.get('available') and osint_data.get('records'):
            for idx, record in enumerate(osint_data.get('records', [])[:5], 1):
                msg += f"\n<blockquote>📌 Record #{idx}"
                if record.get('name'):
                    msg += f"\n   👤 Name: {record.get('name')}"
                if record.get('email'):
                    msg += f"\n   📧 Email: {record.get('email')}"
                if record.get('phone'):
                    msg += f"\n   📱 Phone: {record.get('phone')}"
                if record.get('address'):
                    msg += f"\n   🏠 Address: {record.get('address')[:100]}"
                if record.get('city'):
                    msg += f"\n   🏙️ City: {record.get('city')}"
                if record.get('state'):
                    msg += f"\n   🗺️ State: {record.get('state')}"
                if record.get('dob'):
                    msg += f"\n   🎂 DOB: {record.get('dob')}"
                msg += "</blockquote>"
        else:
            msg += f"\n<blockquote>❌ No OSINT data available for this profile</blockquote>\n"

        msg += f"\n💰 Credits Left: {credits_left}"
        formatted_msg = msg
    else:
        formatted_msg, profile_pic, _ = format_insta_result_v2(result, username, credits_left)

    json_file = save_result_to_json("insta", username, result)
    markup = InlineKeyboardMarkup(row_width=1)

    if json_file:
        file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
        JSON_FILES[file_id] = json_file
        markup.add(create_primary_button("📥 Download JSON", callback_data=f"dljson_{file_id}"))

    if not is_private and recent_posts and len(recent_posts) > 0:
        markup.add(create_success_button(f"📸 VIEW ALL {len(recent_posts)} POSTS", callback_data=f"viewall_{username}"))
        POSTS_CACHE[username] = recent_posts
    elif is_private:
        markup.add(create_default_button("🔒 PRIVATE ACCOUNT - NO POSTS", callback_data="no_posts"))
    else:
        markup.add(create_default_button("📸 NO POSTS AVAILABLE", callback_data="no_posts"))

    markup.add(create_default_button("🔄 REFRESH", callback_data=f"refresh_insta_{username}"))
    markup.add(create_danger_button("❌ CLOSE", callback_data="close_insta"))

    sent_msg = None
    if not is_private and profile_pic and profile_pic.startswith('http'):
        try:
            insta_cap = replace_with_premium_emojis(formatted_msg)
            sent_msg = bot.send_photo(chat_id, profile_pic, caption=insta_cap, reply_markup=markup, parse_mode='HTML')
            try:
                bot.delete_message(chat_id, wait.message_id)
            except:
                pass
        except Exception as e:
            if json_file:
                sent_msg = send_result_with_json(chat_id, formatted_msg, json_file, wait.message_id)
            else:
                sent_msg = send_result(chat_id, formatted_msg, wait)
    else:
        if json_file:
            sent_msg = send_result_with_json(chat_id, formatted_msg, json_file, wait.message_id)
        else:
            sent_msg = send_result(chat_id, formatted_msg, wait)

    if sent_msg:
        send_random_media(chat_id, sent_msg.message_id)

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    admin_panel(message)

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    stats = get_bot_stats()
    msg = f"""
📊 BOT STATISTICS

👑 Total Users: {stats.get('total_users', 0)}
📅 New Today: {stats.get('today_users', 0)}
🟢 Active (24h): {stats.get('active_users', 0)}
💰 Total Credits: {stats.get('total_credits', 0)}
⚡ Commands Used: {stats.get('total_commands', 0)}
👥 Total Referrals: {stats.get('total_referrals', 0)}
"""
    send_with_premium(message.chat.id, msg)

@bot.message_handler(commands=['users'])
def users_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    with db_lock:
        conn = get_db()
        if conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
            admins = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1")
            blocked = c.fetchone()[0]
            conn.close()
            msg = f"""
👥 USER STATISTICS

📊 Total Users: {total}
👑 Admins: {admins}
🚫 Blocked: {blocked}
✅ Active: {total - blocked}
"""
            send_with_premium(message.chat.id, msg)

@bot.message_handler(commands=['add'])
def add_credits_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 3:
        send_with_premium(message.chat.id, "❌ Use: /add [user_id] [credits]")
        return
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
        if add_credits(target_id, amount):
            new_balance = get_credits(target_id)
            send_with_premium(message.chat.id, f"✅ Added {amount} credits to {target_id}\n💰 New Balance: {new_balance}")
            try:
                send_with_premium(target_id, f"✅ Admin added {amount} credits!\n💰 New Balance: {new_balance}")
            except:
                pass
        else:
            send_with_premium(message.chat.id, "❌ Failed to add credits!")
    except ValueError:
        send_with_premium(message.chat.id, "❌ Invalid user ID or amount!")

@bot.message_handler(commands=['removecredit'])
def remove_credits_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 3:
        send_with_premium(message.chat.id, "❌ Use: /removecredit [user_id] [credits]")
        return
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
        with db_lock:
            conn = get_db()
            if conn:
                conn.cursor().execute("UPDATE users SET credits = credits - ? WHERE user_id = ?", (amount, target_id))
                conn.commit()
                conn.close()
                new_balance = get_credits(target_id)
                send_with_premium(message.chat.id, f"✅ Removed {amount} credits from {target_id}\n💰 New Balance: {new_balance}")
    except ValueError:
        send_with_premium(message.chat.id, "❌ Invalid user ID or amount!")

@bot.message_handler(commands=['gen'])
def gen_code_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 4:
        send_with_premium(message.chat.id, "❌ Use: /gen [credits] [max_uses] [days]\nExample: /gen 50 10 30")
        return
    try:
        credits = int(parts[1])
        max_uses = int(parts[2])
        days = int(parts[3])
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        success, result = create_redeem_code(code, credits, max_uses, expiry_date, user_id)
        send_with_premium(message.chat.id, result)
    except ValueError:
        send_with_premium(message.chat.id, "❌ Invalid numbers!")

@bot.message_handler(commands=['deletecode'])
def delete_code_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Usage: `/deletecode [code]`\n💡 Use `/allcodes` to see all codes")
        return
    success, result = delete_redeem_code(parts[1].strip().upper(), user_id)
    send_with_premium(message.chat.id, result)

@bot.message_handler(commands=['allcodes'])
def all_codes_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    with db_lock:
        conn = get_db()
        if conn:
            c = conn.cursor()
            c.execute("SELECT code, credits, max_uses, used_count, expiry_date, is_active FROM redeem_codes ORDER BY id DESC LIMIT 30")
            codes = c.fetchall()
            conn.close()
            if not codes:
                send_with_premium(message.chat.id, "📋 No redeem codes found!")
                return
            msg = "🎫 REDEEM CODES\n\n"
            for code in codes:
                code_str, credits, max_uses, used_count, expiry, active = code
                status = "✅" if active else "❌"
                msg += f"{status} `{code_str}`\n   💰 {credits} credits | Used: {used_count}/{max_uses}\n"
                if expiry:
                    msg += f"   📅 Expires: {expiry[:10]}\n"
                msg += "\n"
            msg += "\n💡 Each code can be used only ONCE per user!\n💡 Use `/deletecode [code]` to delete a code"
            send_with_premium(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(commands=['promote'])
def promote_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Use: /promote [user_id]")
        return
    try:
        target_id = int(parts[1])
        if target_id == ADMIN_ID:
            send_with_premium(message.chat.id, "❌ Cannot promote main owner!")
            return
        with db_lock:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (target_id,))
                conn.commit()
                conn.close()
                send_with_premium(message.chat.id, f"✅ User {target_id} is now an admin!")
                try:
                    send_with_premium(target_id, "✅ You have been promoted to admin!")
                except:
                    pass
    except ValueError:
        send_with_premium(message.chat.id, "❌ Invalid user ID!")

@bot.message_handler(commands=['demote'])
def demote_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Use: /demote [user_id]")
        return
    try:
        target_id = int(parts[1])
        if target_id == ADMIN_ID:
            send_with_premium(message.chat.id, "❌ Cannot demote main owner!")
            return
        with db_lock:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("UPDATE users SET is_admin = 0 WHERE user_id = ?", (target_id,))
                conn.commit()
                conn.close()
                send_with_premium(message.chat.id, f"✅ User {target_id} is no longer an admin!")
                try:
                    send_with_premium(target_id, "❌ You have been demoted from admin!")
                except:
                    pass
    except ValueError:
        send_with_premium(message.chat.id, "❌ Invalid user ID!")

@bot.message_handler(commands=['searchuser'])
def search_user_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Use: /searchuser [id or username]")
        return
    query = parts[1].strip()
    with db_lock:
        conn = get_db()
        if conn:
            c = conn.cursor()
            if query.isdigit():
                c.execute("SELECT * FROM users WHERE user_id = ?", (int(query),))
            else:
                c.execute("SELECT * FROM users WHERE username LIKE ?", (f"%{query}%",))
            user = c.fetchone()
            conn.close()
            if not user:
                send_with_premium(message.chat.id, "❌ User not found!")
                return
            msg = f"""
👤 USER DETAILS

🆔 ID: `{user[0]}`
👤 Username: @{user[1] or 'N/A'}
📝 Name: {user[2] or 'N/A'}
💰 Credits: {user[3] or 0}
👑 Admin: {'✅' if user[4] == 1 else '❌'}
👥 Referrals: {user[6] or 0}
⚡ Commands: {user[9] or 0}
🚫 Blocked: {'✅' if user[12] == 1 else '❌'}
📅 Joined: {str(user[7])[:19] if user[7] else 'N/A'}
"""
            send_with_premium(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(commands=['block'])
def block_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Use: /block [user_id]")
        return
    try:
        target_id = int(parts[1])
        if target_id == ADMIN_ID:
            send_with_premium(message.chat.id, "❌ Cannot block owner!")
            return
        if block_user_in_db(target_id):
            send_with_premium(message.chat.id, f"✅ User {target_id} has been blocked!")
            try:
                send_with_premium(target_id, f"🚫 BANNED 🚫\n\n❌ YOU HAVE BEEN BANNED ❌\n\n📞 Contact Admin: {OWNER_USERNAME}")
            except:
                pass
        else:
            send_with_premium(message.chat.id, "❌ Failed to block user!")
    except ValueError:
        send_with_premium(message.chat.id, "❌ Invalid user ID!")

@bot.message_handler(commands=['unblock'])
def unblock_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split()
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Use: /unblock [user_id]")
        return
    try:
        target_id = int(parts[1])
        if unblock_user_in_db(target_id):
            send_with_premium(message.chat.id, f"✅ User {target_id} has been unblocked!")
            try:
                send_with_premium(target_id, "✅ You have been unblocked! You can use the bot again.")
            except:
                pass
        else:
            send_with_premium(message.chat.id, "❌ Failed to unblock user!")
    except ValueError:
        send_with_premium(message.chat.id, "❌ Invalid user ID!")

@bot.message_handler(commands=['lock'])
def lock_bot_cmd(message):
    global BOT_LOCKED
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    BOT_LOCKED = True
    send_with_premium(message.chat.id, "🔒 BOT LOCKED 🔒\n\n🔐 BOT IS LOCKED BY ADMIN\n\n⏳ Only admins can use the bot now")

@bot.message_handler(commands=['unlock'])
def unlock_bot_cmd(message):
    global BOT_LOCKED
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    BOT_LOCKED = False
    send_with_premium(message.chat.id, "🔓 BOT UNLOCKED 🔓\n\n✅ BOT IS NOW UNLOCKED\n\n🌟 All users can now use the bot")

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return

    broadcast_msg = None
    broadcast_entities = None

    if message.reply_to_message:
        replied = message.reply_to_message
        if replied.text:
            broadcast_msg = replied.text
            broadcast_entities = replied.entities
        elif replied.caption:
            broadcast_msg = replied.caption
            broadcast_entities = replied.caption_entities
        else:
            send_with_premium(message.chat.id, "❌ Replied message has no text or caption!")
            return
    else:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            send_with_premium(message.chat.id, """❌ Use: /broadcast [ᴍᴇssᴀɢᴇ ᴏ🇷 ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ]""")
            return
        broadcast_msg = parts[1]

    all_chats = set()
    with db_lock:
        conn = get_db()
        if conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM users")
            users = c.fetchall()
            for user in users:
                all_chats.add(user[0])
            conn.close()

    try:
        group_chats = get_all_group_chats()
        for gcid in group_chats:
            all_chats.add(gcid)
    except:
        pass

    success_count = 0
    fail_count = 0
    total = len(all_chats)
    progress_msg = send_with_premium(message.chat.id, f"📢 Broadcast started...\n\n📊 Total chats: {total}\n⏳ Sending...")

    for idx, chat_id in enumerate(all_chats, 1):
        try:
            if broadcast_entities:
                bot.send_message(chat_id, broadcast_msg, entities=broadcast_entities, disable_notification=True)
            else:
                send_with_premium(chat_id, broadcast_msg, disable_notification=True)
            success_count += 1
        except Exception as e:
            fail_count += 1

        if idx % 10 == 0:
            try:
                progress_text = f"📢 Broadcast in progress...\n\n📊 Total: {total}\n✅ Sent: {success_count}\n❌ Failed: {fail_count}\n⏳ Progress: {idx}/{total}"
                edit_with_premium(message.chat.id, progress_msg.message_id, progress_text)
            except:
                pass
        time.sleep(0.1)

@bot.message_handler(commands=['uptime'])
def uptime_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    uptime = datetime.now() - BOT_START_TIME
    msg = f"""
🕐 BOT UPTIME

📅 Days: {uptime.days}
⏰ Hours: {uptime.seconds // 3600}
⏱️ Minutes: {(uptime.seconds % 3600) // 60}
⚡ Seconds: {uptime.seconds % 60}
"""
    send_with_premium(message.chat.id, msg)

@bot.message_handler(commands=['commands'])
def commands_stats_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    with db_lock:
        conn = get_db()
        if conn:
            c = conn.cursor()
            c.execute("SELECT user_id, username, total_commands FROM users WHERE total_commands > 0 ORDER BY total_commands DESC LIMIT 10")
            top_users = c.fetchall()
            c.execute("SELECT SUM(total_commands) FROM users")
            total_commands = c.fetchone()[0] or 0
            conn.close()
            msg = "📊 COMMAND USAGE STATS\n\n"
            msg += f"📈 Total Commands: {total_commands}\n\n🏆 TOP USERS:\n"
            for i, user in enumerate(top_users, 1):
                uid, username, cmds = user
                name = f"@{username}" if username else str(uid)
                msg += f"{i}. {name}: {cmds} commands\n"
            send_with_premium(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(commands=['apistatus'])
def apistatus_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        send_with_premium(message.chat.id, """❌ Usage: `/apistatus [command] [status] [message]`""", parse_mode='HTML')
        return

    command = parts[1].lower()
    if command not in API_STATUS:
        send_with_premium(message.chat.id, f"❌ Invalid command!")
        return

    if len(parts) >= 3:
        status_parts = parts[2].split(maxsplit=1)
        status = status_parts[0].lower()
        msg = status_parts[1] if len(status_parts) > 1 else None

        if status == 'working':
            set_api_status(command, True, None)
            send_with_premium(message.chat.id, f"✅ API `/{command}` is now marked as WORKING")
        elif status == 'fixing':
            set_api_status(command, False, msg)
            send_with_premium(message.chat.id, f"⚠️ API `/{command}` is now marked as FIXING")

@bot.message_handler(commands=['addc'])
def add_channel_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Usage: `/addc [channel_url]`", parse_mode='HTML')
        return
    channel_input = parts[1].strip()
    if not validate_channel_url(channel_input):
        send_with_premium(message.chat.id, "❌ Invalid channel URL!", parse_mode='HTML')
        return
    username = extract_username_from_url(channel_input)
    url = f"https://t.me/{username}"
    try:
        bot.get_chat(f"@{username}")
    except Exception as e:
        send_with_premium(message.chat.id, f"❌ Cannot verify channel.")
        return
    success, result = add_force_join_channel(url, username, user_id)
    send_with_premium(message.chat.id, result)

@bot.message_handler(commands=['removec'])
def remove_channel_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        send_with_premium(message.chat.id, "❌ Usage: `/removec [channel_url_or_username]`", parse_mode='HTML')
        return
    success, result = remove_force_join_channel(parts[1].strip(), user_id)
    send_with_premium(message.chat.id, result)

@bot.message_handler(commands=['listc'])
def list_channels_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    channels = list_force_join_channels()
    if not channels:
        send_with_premium(message.chat.id, "📋 No force join channels configured!")
        return
    msg = "\n📢 FORCE JOIN CHANNELS\n\n\n"
    for ch in channels:
        ch_id, url, username, enabled, added_by, added_date = ch
        msg += f"ID: `{ch_id}`\n📢 {url}\n👤 @{username}\n📊 {'✅ Active' if enabled else '❌ Disabled'}\n\n"
    send_with_premium(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(commands=['api'])
def list_apis_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    apis = list_all_apis()
    msg = "\n🔗 API ENDPOINTS\n\n\n"
    for api in apis:
        msg += f"📌 **/{api['command']}**\n   `{api['endpoint'][:80]}...`\n\n"
    send_with_premium(message.chat.id, msg, parse_mode='HTML')

@bot.message_handler(commands=['apic'])
def change_api_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        send_with_premium(message.chat.id, """❌ Usage: `/apic [command] [api_url]`""", parse_mode='HTML')
        return
    command = parts[1].strip().lower().replace('/', '')
    api_url = parts[2].strip()
    success, result = set_api_endpoint(command, api_url, user_id)
    send_with_premium(message.chat.id, result)

@bot.message_handler(commands=['lockf'])
def lock_force_join_cmd(message):
    global FORCE_JOIN_ENABLED
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    FORCE_JOIN_ENABLED = False
    send_with_premium(message.chat.id, "🔓 FORCE JOIN DISABLED 🔓")

@bot.message_handler(commands=['unlockf'])
def unlock_force_join_cmd(message):
    global FORCE_JOIN_ENABLED
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    FORCE_JOIN_ENABLED = True
    send_with_premium(message.chat.id, "🔒 FORCE JOIN ENABLED 🔒")

admin_adding_media = {}

@bot.message_handler(commands=['addvideo'])
def add_video_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    admin_adding_media[user_id] = {"type": "video", "files": []}
    send_with_premium(message.chat.id, "🎬 **BULK VIDEO UPLOAD MODE**\n\nSend me videos and send /done when finished.", parse_mode='HTML')

@bot.message_handler(commands=['addphoto'])
def add_photo_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        send_with_premium(message.chat.id, "❌ Admin only!")
        return
    admin_adding_media[user_id] = {"type": "photo", "files": []}
    send_with_premium(message.chat.id, "🖼️ **BULK PHOTO UPLOAD MODE**\n\nSend me photos and send /done when finished.", parse_mode='HTML')

@bot.message_handler(commands=['done'])
def done_adding_media(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    if user_id not in admin_adding_media:
        send_with_premium(message.chat.id, "❌ No active media session!")
        return
    state = admin_adding_media[user_id]
    files = state["files"]
    media_type = state["type"]
    added = 0
    for idx, file_id in enumerate(files, 1):
        if media_type == "video":
            add_video(file_id, f"Video {idx}", user_id)
        else:
            add_photo(file_id, f"Photo {idx}", user_id)
        added += 1
    del admin_adding_media[user_id]
    send_with_premium(message.chat.id, f"✅ Added {added} {media_type}(s) successfully!")

@bot.message_handler(commands=['cancel'])
def cancel_media_add(message):
    user_id = message.from_user.id
    if user_id in admin_adding_media:
        del admin_adding_media[user_id]
        send_with_premium(message.chat.id, "❌ Cancelled.")

@bot.message_handler(content_types=['video', 'photo'])
def handle_bulk_media(message):
    user_id = message.from_user.id
    if not is_admin(user_id) or user_id not in admin_adding_media:
        return
    state = admin_adding_media[user_id]
    if message.video and state["type"] == "video":
        state["files"].append(message.video.file_id)
        send_with_premium(message.chat.id, f"✅ Video #{len(state['files'])} added!")
    elif message.photo and state["type"] == "photo":
        state["files"].append(message.photo[-1].file_id)
        send_with_premium(message.chat.id, f"✅ Photo #{len(state['files'])} added!")

@bot.message_handler(commands=['delvideo'])
def del_video_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    videos = get_all_videos()
    if not videos:
        send_with_premium(message.chat.id, "📋 No videos found!")
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for vid in videos[:20]:
        markup.add(InlineKeyboardButton(f"🗑️ {vid[2][:30]} (ID: {vid[0]})", callback_data=f"delvid_{vid[0]}"))
    send_with_premium(message.chat.id, "🎬 Select video to delete:", reply_markup=markup)

@bot.message_handler(commands=['delphoto'])
def del_photo_cmd(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    photos = get_all_photos()
    if not photos:
        send_with_premium(message.chat.id, "📋 No photos found!")
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for photo in photos[:20]:
        markup.add(InlineKeyboardButton(f"🗑️ {photo[2][:30]} (ID: {photo[0]})", callback_data=f"delphoto_{photo[0]}"))
    send_with_premium(message.chat.id, "🖼️ Select photo to delete:", reply_markup=markup)

@bot.message_handler(commands=['listvideos'])
def list_videos_cmd(message):
    if not is_admin(message.from_user.id):
        return
    videos = get_all_videos()
    send_with_premium(message.chat.id, f"🎬 Total Videos: {len(videos)}")

@bot.message_handler(commands=['listphotos'])
def list_photos_cmd(message):
    if not is_admin(message.from_user.id):
        return
    photos = get_all_photos()
    send_with_premium(message.chat.id, f"🖼️ Total Photos: {len(photos)}")

@bot.message_handler(commands=['setmode'])
def set_mode_cmd(message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return
    success, result = set_media_mode(parts[1].strip().lower(), message.from_user.id)
    send_with_premium(message.chat.id, result)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vech_page_"))
def vech_page_callback(call):
    try:
        parts = call.data.split("_", 3)
        # format: vech_page_{page_idx}_{user_id}
        if len(parts) < 4:
            bot.answer_callback_query(call.id)
            return
        page_idx = int(parts[2])
        user_id = int(parts[3])

        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ Not your session!", True)
            return

        chat_id = call.message.chat.id
        msg_id = call.message.message_id

        state = VECH_PAGINATION.get(user_id)
        if not state:
            bot.answer_callback_query(call.id, "❌ Session expired. Run command again.", True)
            return

        pages = state["pages"]
        if page_idx < 0 or page_idx >= len(pages):
            bot.answer_callback_query(call.id, "❌ Invalid page.", True)
            return

        state["current"] = page_idx
        text = pages[page_idx]

        markup = InlineKeyboardMarkup(row_width=3)
        buttons = []

        if len(pages) > 1:
            if page_idx > 0:
                buttons.append(create_primary_button(
                    "◀ Prev",
                    callback_data=f"vech_page_{page_idx - 1}_{user_id}",
                    icon_custom_emoji_id="5246794802560774143"
                ))

            buttons.append(create_success_button(
                f"{page_idx + 1}/{len(pages)}",
                callback_data=f"vech_noop_{user_id}",
                icon_custom_emoji_id="5422537279400868395"
            ))

            if page_idx < len(pages) - 1:
                buttons.append(create_danger_button(
                    "Next ▶",
                    callback_data=f"vech_page_{page_idx + 1}_{user_id}",
                    icon_custom_emoji_id="6192763368139397161"
                ))

            markup.row(*buttons)

        json_file = state.get("json_file")
        if page_idx == len(pages) - 1 and json_file:
            file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
            JSON_FILES[file_id] = json_file
            markup.add(InlineKeyboardButton("📥 Download JSON", callback_data=f"dljson_{file_id}"))

        markup.add(create_default_button("🔙 Back", callback_data="back_to_result"))

        try:
            edit_with_premium(chat_id, msg_id, text, reply_markup=markup)
        except Exception as e:
            print(f"Vech pagination edit error: {e}")

        bot.answer_callback_query(call.id, f"📄 Page {page_idx + 1}/{len(pages)}")
    except Exception as e:
        print(f"Vech page callback error: {e}")
        bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("vech_noop_"))
def vech_noop_callback(call):
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("num_page_"))
def num_page_callback(call):
    if call.data == "num_page_noop":
        bot.answer_callback_query(call.id)
        return

    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id  = call.message.message_id

    state = NUM_PAGINATION.get(user_id)
    if not state:
        bot.answer_callback_query(call.id, "❌ Session expired. Run /num again.", True)
        return

    parts    = call.data.split("_", 3)
    page_num = int(parts[2])
    pages    = state["pages"]

    if page_num < 1 or page_num > len(pages):
        bot.answer_callback_query(call.id, "❌ Invalid page.", True)
        return

    txt, markup = pages[page_num - 1]
    json_file = state.get("json_file")
    if page_num == len(pages) and json_file and markup:
        file_id = hashlib.md5(json_file.encode()).hexdigest()[:16]
        JSON_FILES[file_id] = json_file
        markup.add(InlineKeyboardButton("Download JSON", callback_data=f"dljson_{file_id}"))

    try:
        edit_with_premium(chat_id, msg_id, txt, reply_markup=markup)
    except Exception as e:
        print(f"Pagination edit error: {e}")

    bot.answer_callback_query(call.id, f"📄 Page {page_num}/{len(pages)}")

@bot.callback_query_handler(func=lambda call: call.data == "num_dl_json")
def num_dl_json_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    state = NUM_PAGINATION.get(user_id)
    if not state or not state.get("json_file"):
        bot.answer_callback_query(call.id, "❌ Session expired. Run /num again.", True)
        return
    json_file = state["json_file"]
    if os.path.exists(json_file):
        with open(json_file, 'rb') as f:
            bot.send_document(chat_id, f, caption="JSON Export")
        bot.answer_callback_query(call.id, "✅ JSON file sent!")
    else:
        bot.answer_callback_query(call.id, "❌ File not found!", True)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global BOT_LOCKED, FORCE_JOIN_ENABLED
    try:
        if call.data.startswith("dljson_"):
            file_id = call.data.replace("dljson_", "")
            json_file = JSON_FILES.get(file_id)
            if not json_file:
                bot.answer_callback_query(call.id, "❌ File expired or not found!", True)
                return
            if os.path.exists(json_file):
                with open(json_file, 'rb') as f:
                    bot.send_document(call.message.chat.id, f, caption=f"JSON Export")
                bot.answer_callback_query(call.id, "✅ JSON file sent!")
            else:
                bot.answer_callback_query(call.id, "❌ File not found!", True)
            return

        if call.data.startswith("viewall_"):
            username = call.data.replace("viewall_", "")
            posts = POSTS_CACHE.get(username, [])
            if posts:
                bot.answer_callback_query(call.id, f"📸 Sending {len(posts)} posts...")
                send_all_posts(call.message.chat.id, username, posts)
            else:
                bot.answer_callback_query(call.id, "❌ No posts found!", True)
            return

        if call.data == "close_insta" or call.data == "no_posts" or call.data == "close_result":
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            bot.answer_callback_query(call.id)
            return

        if call.data == "back_to_result":
            bot.answer_callback_query(call.id, "✅ Use the command again to see results", True)
            return

        if call.data == "check_join":
            user_id = call.from_user.id
            chat_id = call.message.chat.id
            if check_subscription(user_id):
                bot.answer_callback_query(call.id, "✅ Verification successful!", True)
                try:
                    bot.delete_message(chat_id, call.message.message_id)
                except:
                    pass
            else:
                bot.answer_callback_query(call.id, "❌ Please join all channels first!", True)
            return

        if call.data == "help":
            class FakeMsg:
                def __init__(self, cid, uid):
                    self.chat = type('obj', (), {'id': cid})
                    self.from_user = type('obj', (), {'id': uid})
                    self.text = "/help"
                    self.date = int(datetime.now().timestamp())
            help_cmd(FakeMsg(call.message.chat.id, call.from_user.id))
            bot.answer_callback_query(call.id)
            return

        if call.data == "profile":
            class FakeMsg:
                def __init__(self, cid, uid):
                    self.chat = type('obj', (), {'id': cid})
                    self.from_user = type('obj', (), {'id': uid})
                    self.text = "/profile"
                    self.date = int(datetime.now().timestamp())
            profile_cmd(FakeMsg(call.message.chat.id, call.from_user.id))
            bot.answer_callback_query(call.id)
            return

        if call.data == "balance":
            class FakeMsg:
                def __init__(self, cid, uid):
                    self.chat = type('obj', (), {'id': cid})
                    self.from_user = type('obj', (), {'id': uid})
                    self.text = "/balance"
                    self.date = int(datetime.now().timestamp())
            balance_cmd(FakeMsg(call.message.chat.id, call.from_user.id))
            bot.answer_callback_query(call.id)
            return

        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"❌ Callback error: {e}")

@bot.message_handler(func=lambda m: True)
def track_all_messages(m):
    if m.chat.type in ['group', 'supergroup']:
        chat_id = m.chat.id
        chat_title = m.chat.title or "Unknown"
        chat_type = m.chat.type
        with db_lock:
            conn = get_db()
            if conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO group_chats (chat_id, chat_title, chat_type, added_date, last_active, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                         (chat_id, chat_title, chat_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
                conn.commit()
                conn.close()

def create_session():
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=20,
        pool_maxsize=20,
        max_retries=Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504]),
        pool_block=False
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive'
    })
    return session

session = create_session()

def is_recent_command(message):
    if is_admin(message.from_user.id):
        return True
    msg_time = datetime.fromtimestamp(message.date)
    if msg_time < BOT_START_TIME:
        return False
    return True

def clear_pending_updates():
    global LAST_PROCESSED_UPDATE_ID
    try:
        updates = bot.get_updates(limit=1, timeout=1)
        if updates:
            LAST_PROCESSED_UPDATE_ID = updates[-1].update_id
            bot.get_updates(offset=LAST_PROCESSED_UPDATE_ID + 1, limit=1, timeout=1)
    except Exception as e:
        pass

if __name__ == "__main__":
    print("=" * 60)
    print("✅ OSINT BOT STARTING WITH ALL FIXES...")
    print("✅ Developer: ⏤͟͟͞͞RAJPUT BHAI")
    print("=" * 60)

    try:
        bot.remove_webhook()
    except:
        pass

    clear_pending_updates()

    try:
        bot.polling(non_stop=True, skip_pending=True, timeout=30)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔄 Restarting in 3 seconds...")
        time.sleep(3)
        os.execv(sys.executable, [sys.executable] + sys.argv)
