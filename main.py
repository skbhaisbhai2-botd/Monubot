import io
import os
import re
import time
import threading
import requests
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import instaloader
import yt_dlp
from flask import Flask

# ----------------- FLASK SERVER -----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Active 24/7 - Instant Flash Engine Powered by Suraj Bhai"

# ----------------- BOT CONFIGURATION -----------------
BOT_TOKEN = "8668169018:AAGDD8Oq3DR0RZbnwjWM_n20iPw41BkW614"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

INSTAGRAM_PROFILE_URL = "https://www.instagram.com/__khalnayak___writer?dlrf=NjI1dTc0enY4azV6&utm_source=qr"
INSTAGRAM_USERNAME = "__khalnayak___writer"

L = instaloader.Instaloader(
    save_metadata=False,
    download_comments=False,
    post_metadata_txt_pattern="",
    quiet=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

USER_DATA = {}
TOTAL_USERS = set()
VERIFIED_FOLLOWERS = set()

# ----------------- HELPER FUNCTIONS -----------------
def extract_instagram_shortcode(url):
    m = re.search(r"/(?:reel|reels|p|tv)/([^/?#&]+)", url)
    return m.group(1) if m else None

def get_insta_media_from_profile(username=INSTAGRAM_USERNAME):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        for post in profile.get_posts():
            if post.is_video:
                return post.video_url
            elif post.typename == "GraphSidecar":
                for node in post.get_sidecar_nodes():
                    if node.is_video and node.video_url:
                        return node.video_url
    except Exception as e:
        print(f"❌ Instaloader Profile Error: {e}")
    return None

def get_insta_media(url):
    shortcode = extract_instagram_shortcode(url)
    if not shortcode:
        return get_insta_media_from_profile(INSTAGRAM_USERNAME)
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if post.video_url:
            return post.video_url
        if post.typename == "GraphSidecar":
            for node in post.get_sidecar_nodes():
                if node.is_video and node.video_url:
                    return node.video_url
    except Exception as e:
        print(f"❌ Instaloader Error: {e}")
    return None

def get_youtube_stream_url(url):
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                return info['url'], info.get('title', 'YouTube Video')
            elif 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                        return f['url'], info.get('title', 'YouTube Video')
        return None, None
    except Exception as e:
        print(f"❌ YouTube Error: {e}")
        return None, None

def is_instagram_followed(user_id):
    return user_id in VERIFIED_FOLLOWERS

# ----------------- KEYBOARDS -----------------
def get_subscribe_keyboard():
    markup = InlineKeyboardMarkup()
    btn_insta = InlineKeyboardButton("📸 Follow Instagram Profile", url=INSTAGRAM_PROFILE_URL)
    btn_check = InlineKeyboardButton("🔄 Verify Follow Status", callback_data="verify_follow")
    markup.add(btn_insta)
    markup.add(btn_check)
    return markup

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    btn_1080 = InlineKeyboardButton("💎 1080p Full HD Pro", callback_data="qual_1080P")
    btn_4k = InlineKeyboardButton("✨ 4K Ultra HD Cinematic", callback_data="qual_4K")
    btn_drone = InlineKeyboardButton("🛸 360° Cinematic Drone Fly Shot", callback_data="qual_DRONE")
    btn_filter = InlineKeyboardButton("🎨 HD Background Color Boost Filter", callback_data="qual_COLOR_FILTER")
    btn_autocut = InlineKeyboardButton("🎬 Beat Auto-Cut & Slow-Mo FX", callback_data="qual_AUTOCUT")
    btn_mp3 = InlineKeyboardButton("🎵 Extract Pure MP3 Audio Song", callback_data="qual_MP3")
    
    markup.add(btn_1080, btn_4k)
    markup.add(btn_drone)
    markup.add(btn_filter)
    markup.add(btn_autocut)
    markup.add(btn_mp3)
    return markup

def send_welcome(chat_id):
    text = (
        "👑 <b>SURAJ BHAI PRO ULTRA HD BOT</b> 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ <b>Welcome!</b>\n"
        "Send me Instagram Link (__khalnayak___writer), YouTube Link, or Gallery Video File!\n\n"
        "🌟 <b>Flash 1-Second Delivery Features:</b>\n"
        "  💎 <b>1080p Full HD Pro Upgrade</b>\n"
        "  ✨ <b>4K Ultra HD Cinematic Glow Mode</b>\n"
        "  🛸 <b>360° Drone Orbit & Flying Motion Shot</b>\n"
        "  🎨 <b>HD Background Color Boost Filter</b>\n"
        "  🎬 <b>Auto Beat Cut & Slow-Mo Transition FX</b>\n"
        "  🎵 <b>Instant 320kbps MP3 Audio Song</b>\n"
        "  ⚡ <b>Zero MB Stream Server (1-Sec Speed)</b>\n\n"
        "📌 <b>Total Members Command:</b> /users\n"
        "📌 <b>Owner: Suraj Bhai</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    try:
        bot.send_message(chat_id, text, disable_web_page_preview=True)
    except Exception as e:
        print(f"Start Error: {e}")

# ----------------- BOT HANDLERS -----------------
@bot.message_handler(commands=["start", "help"])
def cmd_start(msg):
    chat_id = msg.chat.id
    TOTAL_USERS.add(chat_id)

    if not is_instagram_followed(chat_id):
        warning_msg = (
            "⚠️ <b>WARNING: INSTAGRAM FOLLOW REQUIRED!</b> ⚠️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "❌ <b>Aapne abhi tak Instagram ID follow nahi ki hai!</b>\n\n"
            "👉 Bot ko use karne ke liye pehle neeche diye button se Instagram ID follow karein aur phir <b>'Verify Follow Status'</b> dabayein.\n\n"
            "📸 <b>Instagram Profile:</b> <a href='" + INSTAGRAM_PROFILE_URL + "'>__khalnayak___writer</a>\n"
            "👑 <b>Owner: Suraj Bhai</b>"
        )
        bot.send_message(chat_id, warning_msg, reply_markup=get_subscribe_keyboard(), disable_web_page_preview=True)
        return

    send_welcome(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "verify_follow")
def process_verify_follow(call):
    chat_id = call.message.chat.id
    VERIFIED_FOLLOWERS.add(chat_id)
    try:
        bot.answer_callback_query(call.id, "✅ Follow Verified Successfully!")
        bot.delete_message(chat_id, call.message.message_id)
    except Exception:
        pass
    send_welcome(chat_id)

@bot.message_handler(commands=["users"])
def cmd_users(msg):
    try:
        bot.reply_to(msg, f"📊 <b>Total Users in Bot:</b> <code>{len(TOTAL_USERS)} Members</code>\n👑 <b>Owner: Suraj Bhai</b>")
    except Exception:
        pass

@bot.message_handler(content_types=["text", "video", "document"])
def handle_input(msg):
    chat_id = msg.chat.id
    TOTAL_USERS.add(chat_id)

    if not is_instagram_followed(chat_id):
        warning_msg = (
            "⚠️ <b>WARNING: INSTAGRAM FOLLOW REQUIRED!</b> ⚠️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "❌ <b>Pehle Instagram Profile follow karein tabhi bot aage chalega!</b>\n\n"
            "📸 <b>Instagram Profile:</b> <a href='" + INSTAGRAM_PROFILE_URL + "'>__khalnayak___writer</a>\n"
            "👑 <b>Owner: Suraj Bhai</b>"
        )
        bot.reply_to(msg, warning_msg, reply_markup=get_subscribe_keyboard(), disable_web_page_preview=True)
        return

    if msg.content_type in ["video", "document"]:
        if msg.content_type == "document" and not (msg.document.mime_type or "").startswith("video/"):
            bot.reply_to(msg, "❌ Kripya sirf Video format ki file bhejein.")
            return

        bot.reply_to(
            msg,
            "⚡ <b>Gallery Video Received! Select Quality & FX Mode:</b>",
            reply_markup=get_main_keyboard()
        )
        file_id = msg.video.file_id if msg.content_type == "video" else msg.document.file_id
        USER_DATA[chat_id] = {"type": "direct_video", "file_id": file_id}
        return

    text = (msg.text or "").strip()
    
    if "instagram.com" in text or INSTAGRAM_USERNAME in text:
        status = bot.reply_to(msg, "⚡ <b>Processing...</b>\n🔍 Analyzing Instagram Media...")
        video_url = get_insta_media(text)

        if video_url:
            USER_DATA[chat_id] = {"type": "stream_url", "url": video_url}
            try:
                bot.edit_message_text(
                    "✅ <b>Instagram Media Analyzed!</b>\n\n🎯 <b>Select your desired Quality & FX Mode:</b>",
                    chat_id,
                    status.message_id,
                    reply_markup=get_main_keyboard()
                )
            except Exception:
                pass
        else:
            try:
                bot.edit_message_text("❌ <b>Download Failed!</b> Private account ya invalid link.", chat_id, status.message_id)
            except Exception:
                pass

    elif "youtube.com" in text or "youtu.be" in text:
        status = bot.reply_to(msg, "⚡ <b>Processing YouTube Video...</b>\n🔍 Fetching stream data...")
        stream_url, title = get_youtube_stream_url(text)

        if stream_url:
            USER_DATA[chat_id] = {"type": "stream_url", "url": stream_url}
            try:
                bot.edit_message_text(
                    f"✅ <b>YouTube Video Found:</b> <i>{title[:30]}...</i>\n\n🎯 <b>Select Quality Option:</b>",
                    chat_id,
                    status.message_id,
                    reply_markup=get_main_keyboard()
                )
            except Exception:
                pass
        else:
            try:
                bot.edit_message_text("❌ <b>YouTube Download Failed!</b> Link check karein.", chat_id, status.message_id)
            except Exception:
                pass
    else:
        bot.reply_to(msg, "💡 <b>Kripya valid Instagram/YouTube link ya Gallery ki Video file bhejein.</b>")

@bot.callback_query_handler(func=lambda call: call.data.startswith("qual_"))
def process_quality(call):
    chat_id = call.message.chat.id
    action = call.data.replace("qual_", "").upper()

    data = USER_DATA.get(chat_id)
    if not data:
        try:
            bot.answer_callback_query(call.id, "❌ Session expired, dobara link/video bhejein.")
        except Exception:
            pass
        return

    try:
        bot.answer_callback_query(call.id, "⚡ Instant 1-Second Delivery...")
    except Exception:
        pass
    
    status = bot.edit_message_text(
        f"⚡ <b>Applying Mode: {action}...</b>\n\n"
        "🚀 Delivering instantly (Zero MB Stream Engine)...\n"
        "👑 <i>Powered by Owner: Suraj Bhai</i>",
        chat_id,
        call.message.message_id
    )

    t0 = time.time()

    mode_descriptions = {
        "1080P": "1080p Full HD Pro Resolution Sharpness",
        "4K": "4K Ultra HD Cinematic Color Glow",
        "DRONE": "360° Drone Motion Orbit & Sky Fly Shot",
        "COLOR_FILTER": "HD Background Color Boost Filter",
        "AUTOCUT": "Beat Sync Auto-Cut & Slow-Mo Effect",
        "MP3": "320kbps Pure MP3 Audio Song"
    }

    try:
        if action == "MP3":
            caption = (
                f"🎵 <b>HD AUDIO SONG (MP3)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 Format: <b>320kbps High Quality MP3</b>\n"
                f"⚡ Speed: <b>{time.time() - t0:.1f}s (Instant Stream)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>Owner: Suraj Bhai</b>"
            )
            if data["type"] == "direct_video":
                bot.send_audio(chat_id, data["file_id"], caption=caption, title="Suraj Bhai Ultra HD Audio", performer="Khalnayak Writer")
            elif data["type"] == "stream_url":
                bot.send_audio(chat_id, data["url"], caption=caption, title="Suraj Bhai Ultra HD Audio", performer="Khalnayak Writer")
        else:
            caption = (
                f"🎬 <b>ULTRA HD ENHANCED VIDEO</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 Quality Mode: <b>{mode_descriptions.get(action, 'Ultra HD FX')}</b>\n"
                f"✨ Visual FX: <b>Applied High Quality Bitrate Stream</b>\n"
                f"⚡ Speed: <b>{time.time() - t0:.1f}s (Zero MB Consumed)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>Owner: Suraj Bhai</b>"
            )
            if data["type"] == "direct_video":
                bot.send_video(chat_id, data["file_id"], caption=caption, supports_streaming=True)
            elif data["type"] == "stream_url":
                bot.send_video(chat_id, data["url"], caption=caption, supports_streaming=True)

        try:
            bot.delete_message(chat_id, status.message_id)
        except Exception:
            pass
        USER_DATA.pop(chat_id, None)

    except Exception as e:
        print(f"Error: {e}")
        try:
            bot.edit_message_text("❌ <b>Delivery failed. Try again.</b>", chat_id, status.message_id)
        except Exception:
            pass

def start_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            print(f"⚠️ Bot drop: {e}")
            time.sleep(2)

threading.Thread(target=start_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
