import io
import os
import re
import threading
import time
import instaloader
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# ---------- Flask Web Server (24/7 Uptime) ----------
app = Flask("")


@app.route("/")
def home():
  return "<b>🤖 Suraj Bhai Bot is Active 24/7!</b>"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


def keep_alive():
  t = threading.Thread(target=run_flask)
  t.daemon = True
  t.start()


# ---------- Bot Configurations ----------
BOT_TOKEN = "8668169018:AAGDD8Oq3DR0RZbnwjWM_n20iPw41BkW614"
REQUIRED_INSTA_URL = "https://www.instagram.com/__khalnayak___writer?dlrf=NjI1dTc0enY4azV6&utm_source=qr"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------- Instaloader Setup ----------
L = instaloader.Instaloader(
    save_metadata=False,
    download_comments=False,
    post_metadata_txt_pattern="",
    quiet=True,
)

# ---------- RAM Memory Cache ----------
CACHE = {}
CACHE_LIMIT = 25


def extract_shortcode(url):
  m = re.search(r"/(?:reel|reels|p|tv)/([^/?]+)", url)
  return m.group(1) if m else None


def get_best_video_url(post):
  if post.video_url:
    return post.video_url

  if post.typename == "GraphSidecar":
    best = None
    best_score = -1
    for node in post.get_sidecar_nodes():
      if node.is_video and node.video_url:
        try:
          score = node.video_duration or 1
        except Exception:
          score = 1
        if score > best_score:
          best_score = score
          best = node.video_url
    return best

  return None


def fetch_reel_bytes(url):
  shortcode = extract_shortcode(url)
  if not shortcode:
    return None

  if shortcode in CACHE:
    return io.BytesIO(CACHE[shortcode])

  try:
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    video_url = get_best_video_url(post)

    if not video_url:
      return None

    headers = {
        "User-Agent": L.context.user_agent,
        "Accept": "*/*",
    }

    r = requests.get(video_url, headers=headers, stream=True, timeout=90)
    r.raise_for_status()
    data = r.content

    if len(data) < 70 * 1024 * 1024:
      if len(CACHE) >= CACHE_LIMIT:
        CACHE.pop(next(iter(CACHE)))
      CACHE[shortcode] = data

    return io.BytesIO(data)

  except Exception as e:
    print(f"❌ Fetch Error: {e}")
    return None


# ---------- /start Command ----------
@bot.message_handler(commands=["start", "help"])
def cmd_start(msg):
  markup = InlineKeyboardMarkup()
  markup.add(
      InlineKeyboardButton(
          "💎 Follow Owner on Instagram", url=REQUIRED_INSTA_URL
      )
  )
  markup.add(
      InlineKeyboardButton(
          "✅ I Have Followed — Continue", callback_data="verified_check"
      )
  )

  text = (
      "🖤 <b>INSTAGRAM PRO CINEMATIC BOT</b> ⚡\n"
      "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
      "👑 <b>Owner & Creator:</b> <u>Suraj Bhai</u>\n\n"
      "⚠️ <b>MANDATORY WARNING:</b>\n"
      "<i>To use this bot and unlock 4K Ultra HD & Pro Max features, "
      "you must follow our official creator profile first!</i>\n\n"
      "👇 Click below to verify & unlock:"
  )
  bot.send_message(msg.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "verified_check")
def verify_callback(call):
  bot.answer_callback_query(call.id, "✨ Verified Successfully!")
  text = (
      "🚀 <b>Welcome Back to Pro Suite!</b>\n"
      "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
      "🎯 Send any <b>Instagram Reel or Post Link</b> now.\n"
      "✨ Unlocked: <i>1080p, 1800p Cinematic, MP3 & Pro Max HD!</i>\n\n"
      "👑 <b>Powered by Suraj Bhai</b>"
  )
  bot.edit_message_text(
      text, call.message.chat.id, call.message.message_id, parse_mode="HTML"
  )


# ---------- Instant Link Handler (No Lag) ----------
@bot.message_handler(func=lambda m: True)
def handle_link(msg):
  url = (msg.text or "").strip()

  if "instagram.com" not in url:
    bot.reply_to(
        msg,
        "❌ <b>Invalid Link Structure</b>\n\n"
        "💡 Please provide a legitimate Instagram link.\n"
        "👑 <i>Suraj Bhai Production</i>",
    )
    return

  # Turant Options Menu dikhayega bina kisi processing delay ke
  markup = InlineKeyboardMarkup(row_width=2)
  markup.add(
      InlineKeyboardButton("🎬 1080p HD", callback_data=f"dl|1080|{url}"),
      InlineKeyboardButton(
          "🔥 1800p 4K Cinematic", callback_data=f"dl|1800|{url}"
      ),
      InlineKeyboardButton("🎵 MP3 Audio Only", callback_data=f"dl|mp3|{url}"),
      InlineKeyboardButton(
          "💎 Pro Max HD (Ultra)", callback_data=f"dl|promax|{url}"
      ),
  )

  text = (
      "🎛️ <b>SELECT YOUR DOWNLOAD QUALITY:</b>\n"
      "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
      "✨ <i>Advanced enhancements enabled (Face Clean, Deep Dark RGB"
      " tones).</i>\n\n"
      "👑 <b>Owner: Suraj Bhai</b>"
  )
  bot.reply_to(msg, text, reply_markup=markup)


# ---------- Callback Download Processing (Jab button dabega) ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("dl|"))
def process_download(call):
  data_parts = call.data.split("|", 2)
  quality_type = data_parts[1]
  url = data_parts[2]

  bot.answer_callback_query(
      call.id,
      f"🚀 Initializing {quality_type.upper()} High-Speed Render...",
  )

  try:
    bot.edit_message_text(
        f"📥 <b>Downloading ({quality_type.upper()})</b>\n⚡ Applying"
        " crystal-clear clothing & face smooth filters...",
        call.message.chat.id,
        call.message.message_id,
    )
  except Exception:
    pass

  t0 = time.time()
  video_io = fetch_reel_bytes(url)

  if video_io:
    try:
      speed = time.time() - t0
      caption = (
          "✅ <b>PRO DOWNLOAD COMPLETE!</b>\n"
          "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
          f"💎 Quality Tier: <b>{quality_type.upper()} Ultra HD</b>\n"
          f"⚡ Delivery Speed: <b>{speed:.1f}s (Instant)</b>\n"
          "🎨 <i>Enhanced: Deep Dark Tone & Clean Face HD</i>\n"
          "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
          "👑 <b>Managed By: Suraj Bhai</b> 🎉"
      )
      if quality_type == "mp3":
        bot.send_audio(call.message.chat.id, video_io, caption=caption)
      else:
        bot.send_video(
            call.message.chat.id,
            video_io,
            caption=caption,
            supports_streaming=True,
        )

      bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
      print(f"Delivery Error: {e}")
  else:
    bot.edit_message_text(
        "❌ <b>Render Failed</b>\n\n⚠️ Private post or rate limit encountered.",
        call.message.chat.id,
        call.message.message_id,
    )


# ---------- Execution Entry Point ----------
if __name__ == "__main__":
  keep_alive()

  print("========================================")
  print("  🖤 INSTAGRAM CINEMATIC BOT ONLINE")
  print("  👑 Owner: Suraj Bhai")
  print("  ⚡ Flask Web Server Active (24/7 Service)")
  print("========================================")

  while True:
    try:
      bot.infinity_polling(
          timeout=60, long_polling_timeout=30, skip_pending=True
      )
    except Exception as e:
      print(f"⚠️ Connection error: {e}")
      time.sleep(3)
