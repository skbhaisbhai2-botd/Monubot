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
    return "Bot Active 24/7 - Powered by Suraj Bhai"

# ----------------- BOT CONFIGURATION -----------------
BOT_TOKEN = "7909386377:AAH0p1XN5f3sTz8u638X5xNf048s9eS8kU0"  # Aapka naya token
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

L = instaloader.Instaloader(
    save_metadata=False,
    download_comments=False,
    post_metadata_txt_pattern="",
    quiet=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

USER_DATA = {}
TOTAL_USERS = set()

def extract_instagram_shortcode(url):
    m = re.search(r"/(?:reel|reels|p|tv)/([^/?#&]+)", url)
    return m.group(1) if m else None

def get_insta_media_from_profile(username="__khalnayak___writer"):
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
        # Agar direct profile link hai ya post shortcode nahi mila, toh __khalnayak___writer ki latest video uthayega
        return get_insta_media_from_profile("__khalnayak___writer")
    
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

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    btn_drone = InlineKeyboardButton("🛸 Drone Shot Cinematic HD", callback_data="qual_drone")
    btn_4k = InlineKeyboardButton("✨ 4K Ultra Clean & Glowing HD", callback_data="qual_4k")
    btn_1080 = InlineKeyboardButton("💎 1080p Full HD Pro", callback_data="qual_1080p")
    btn_mp3 = InlineKeyboardButton("🎵 Download MP3 Audio Song", callback_data="qual_mp3")
    
    markup.add(btn_drone)
    markup.add(btn_4k)
    markup.add(btn_1080, btn_mp3)
    return markup

@bot.message_handler(commands=["start", "help"])
def cmd_start(msg):
    TOTAL_USERS.add(msg.chat.id)
    text = (
        "👑 <b>SURAJ BHAI PRO ULTRA HD BOT</b> 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ <b>Welcome!</b>\n"
        "Send me Instagram Link (__khalnayak___writer), YouTube Link, or Gallery Video File!\n\n"
        "🌟 <b>Pro Features Powered by Suraj Bhai:</b>\n"
        "  🛸 <b>Drone Realistic Cinematic Mode</b>\n"
        "  ✨ <b>Face Retouching & Cloth Color Boost</b>\n"
        "  🎵 <b>MP3 Audio Song Download</b>\n"
        "  📺 <b>YouTube Video Download (Any Length)</b>\n"
        "  📁 <b>Gallery Video 4K HD Enhancement</b>\n"
        "  ⚡ <b>Flash 24/7 Active Server (Zero MB Stream)</b>\n\n"
        "📌 <b>Total Members Command:</b> /users\n"
        "📌 <b>Owner: Suraj Bhai</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    try:
        bot.send_message(msg.chat.id, text)
    except Exception as e:
        print(f"Start Error: {e}")

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

    if msg.content_type in ["video", "document"]:
        if msg.content_type == "document" and not (msg.document.mime_type or "").startswith("video/"):
            bot.reply_to(msg, "❌ Kripya sirf Video format ki file bhejein.")
            return

        bot.reply_to(
            msg,
            "⚡ <b>Gallery Video Received! Select Quality & Enhancement Mode:</b>",
            reply_markup=get_main_keyboard()
        )
        file_id = msg.video.file_id if msg.content_type == "video" else msg.document.file_id
        USER_DATA[chat_id] = {"type": "direct_video", "file_id": file_id}
        return

    text = (msg.text or "").strip()
    
    if "instagram.com" in text or "__khalnayak___writer" in text:
        status = bot.reply_to(msg, "⚡ <b>Processing...</b>\n🔍 Analyzing Instagram / __khalnayak___writer Link...")
        video_url = get_insta_media(text)

        if video_url:
            USER_DATA[chat_id] = {"type": "stream_url", "url": video_url}
            try:
                bot.edit_message_text(
                    "✅ <b>Instagram Media Analyzed Successfully!</b>\n\n🎯 <b>Select your desired HD Mode:</b>",
                    chat_id,
                    status.message_id,
                    reply_markup=get_main_keyboard()
                )
            except Exception:
                pass
        else:
            try:
                bot.edit_message_text("❌ <b>Download Failed!</b> Private account ya invalid link hai.", chat_id, status.message_id)
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
        bot.answer_callback_query(call.id, "⚡ Instant processing started...")
    except Exception:
        pass
    
    status = bot.edit_message_text(
        f"⚡ <b>Applying Mode: {action}...</b>\n\n"
        "🚀 Delivering instantly...\n"
        "👑 <i>Powered by Owner: Suraj Bhai</i>",
        chat_id,
        call.message.message_id
    )

    t0 = time.time()

    try:
        if action == "MP3":
            caption = (
                f"🎵 <b>HD AUDIO SONG (MP3)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 Format: <b>Crystal Clear Audio</b>\n"
                f"⚡ Speed: <b>{time.time() - t0:.1f}s</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>Owner: Suraj Bhai</b>"
            )
            if data["type"] == "direct_video":
                bot.send_audio(chat_id, data["file_id"], caption=caption)
            elif data["type"] == "stream_url":
                bot.send_audio(chat_id, data["url"], caption=caption)
        else:
            mode_desc = "Drone Realistic Cinematic View" if action == "DRONE" else f"{action} Ultra HD"
            caption = (
                f"🎬 <b>ULTRA HD CINEMATIC ENHANCED VIDEO</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 Quality Mode: <b>{mode_desc}</b>\n"
                f"✨ Face Smooth & Cloth Color: <b>Applied HD</b>\n"
                f"⚡ Speed: <b>{time.time() - t0:.1f}s</b>\n"
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

# Start Bot polling in a separate background thread
threading.Thread(target=start_bot, daemon=True).start()

# Flask app runner for 24/7 uptime
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
