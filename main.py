import telebot
import requests
import whois
import yt_dlp
import qrcode
import os
import random
import string
import json
import time
from datetime import datetime
from gtts import gTTS
from faker import Faker

# ==========================================
# CONFIGURATION
# ==========================================
API_TOKEN = '8047418906:AAE0W9SgllpX7dFR6iIoum9ixjMijFij-pc'
bot = telebot.TeleBot(API_TOKEN)

# Downloads folder ဆောက်ခြင်း
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Faker Objects
fake_us = Faker('en_US')
fake_jp = Faker('ja_JP')
fake_th = Faker('th_TH')

print("🤖 All-in-One Bot is starting...")

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def is_youtube_url(text):
    # Command မဟုတ်ဘဲ Link သီးသန့်ဖြစ်မှ True ပြန်မယ်
    return ("youtube.com" in text or "youtu.be" in text) and not text.startswith('/')

def is_tiktok_url(text):
    return "tiktok.com" in text and not text.startswith('/')

def format_date(date_obj):
    if isinstance(date_obj, list):
        return date_obj[0].strftime('%Y-%m-%d')
    elif isinstance(date_obj, datetime):
        return date_obj.strftime('%Y-%m-%d')
    else:
        return "N/A"

def translate_text_google(target_lang, text):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            translated = "".join([s[0] for s in data[0] if s[0]])
            return translated
        return text
    except:
        return text

# ==========================================
# 1. UTILITY COMMANDS (Whois, IP, QR, Rate)
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = """
🤖 **Bot Commands List**

🎵 **Media:**
• Send YouTube Link -> Download MP3
• Send TikTok Link -> Download Video
• `/mp3 [name]` -> Search & Download Song
• `/mp3 [link]` -> Download MP3 from Link

🛠 **Tools:**
• `/whois [domain]` -> Domain Info
• `/ip [address]` -> IP Info
• `/qr [text]` -> Create QR Code
• `/ss [url]` -> Website Screenshot
• `/tr [lang] [text]` -> Translate
• `/say [lang] [text]` -> Text to Speech
• `/img [text]` -> AI Image Generator

💰 **Finance:**
• `/rate` -> Myanmar Currency Exchange
• `/p [coin]` -> Crypto Price (e.g. /p btc)

👤 **Identity:**
• `/fake [us/jp/th]` -> Fake ID
• `/bin [6-digits]` -> Check/Gen Credit Card
• `/new` -> Get Temp Email
• `/check` -> Check Email Inbox

📸 **Other:**
• Send Photo -> Get Image Link
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['whois', 'domain'])
def check_domain(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Domain Name ထည့်ပါ\nExample: `/whois google.com`", parse_mode='Markdown')
            return
        domain = parts[1].lower()
        msg = bot.reply_to(message, f"🔍 Checking {domain}...")
        
        w = whois.whois(domain)
        if not w.domain_name:
            bot.edit_message_text("❌ Domain Not Found", message.chat.id, msg.message_id)
            return

        reply_text = (
            f"🌐 <b>Domain Info:</b> {domain.upper()}\n"
            f"🏢 Registrar: {w.registrar}\n"
            f"📅 Created: {format_date(w.creation_date)}\n"
            f"⏳ Expires: {format_date(w.expiration_date)}"
        )
        bot.edit_message_text(reply_text, message.chat.id, msg.message_id, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['ip'])
def get_ip_info(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "IP ထည့်ပါ (Ex: /ip 8.8.8.8)")
            return
        ip = parts[1]
        res = requests.get(f"http://ip-api.com/json/{ip}").json()
        if res['status'] == 'success':
            bot.reply_to(message, f"🌍 IP: {ip}\n🏳️ Country: {res['country']}\nISP: {res['isp']}")
        else:
            bot.reply_to(message, "IP ရှာမတွေ့ပါ။")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['qr'])
def generate_qr(message):
    data = ""
    if message.reply_to_message and message.reply_to_message.text:
        data = message.reply_to_message.text
    elif len(message.text.split()) > 1:
        data = message.text.split(maxsplit=1)[1]
    else:
        bot.reply_to(message, "စာရိုက်ထည့်ပါ (Ex: /qr Hello)")
        return

    img = qrcode.make(data)
    filename = f"downloads/qr_{message.chat.id}.png"
    img.save(filename)
    with open(filename, 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption="📱 QR Code Generated")
    os.remove(filename)

@bot.message_handler(commands=['rate'])
def get_exchange_rate(message):
    try:
        data = requests.get("https://forex.cbm.gov.mm/api/latest").json()
        rates = data['rates']
        txt = f"📅 <b>Rates ({data['info']})</b>\n🇺🇸 USD: {rates.get('USD')} MMK\n🇪🇺 EUR: {rates.get('EUR')} MMK\n🇸🇬 SGD: {rates.get('SGD')} MMK\n🇹🇭 THB: {rates.get('THB')} MMK"
        bot.reply_to(message, txt, parse_mode='HTML')
    except:
        bot.reply_to(message, "Connection Error")

@bot.message_handler(commands=['price', 'p'])
def crypto_price(message):
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "/p [coin] (Ex: /p btc)")
    coin = parts[1].lower()
    coin_map = {'btc': 'bitcoin', 'eth': 'ethereum', 'bnb': 'binancecoin', 'usdt': 'tether'}
    coin_id = coin_map.get(coin, coin)
    
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url).json()
        if coin_id in data:
            d = data[coin_id]
            symbol = "🟢" if d['usd_24h_change'] > 0 else "🔴"
            bot.reply_to(message, f"💰 <b>{coin.upper()}</b>: ${d['usd']:,.2f}\n{symbol} 24h: {d['usd_24h_change']:.2f}%", parse_mode='HTML')
        else:
            bot.reply_to(message, "Coin Not Found")
    except:
        bot.reply_to(message, "API Error")

@bot.message_handler(commands=['ss'])
def screenshot(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return bot.reply_to(message, "Link ထည့်ပါ (Ex: /ss google.com)")
    url = parts[1]
    bot.send_chat_action(message.chat.id, 'upload_photo')
    api = f"https://s0.wp.com/mshots/v1/{url}?w=1280&h=720"
    bot.send_photo(message.chat.id, requests.get(api).content, caption=f"📸 {url}")

# ==========================================
# 2. MEDIA & AI (MP3, TTS, Image, Translate)
# ==========================================

@bot.message_handler(commands=['mp3', 'song'])
def smart_mp3_handler(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "သီချင်းနာမည် သို့မဟုတ် Link ထည့်ပါ\nEx: `/mp3 Lay Phyu` OR `/mp3 https://youtu.be/...`", parse_mode='Markdown')
        return
    
    query = parts[1]
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, f"🔎 Processing: {query}...")

    # Options for yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'quiet': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Check if URL or Search
            if "youtube.com" in query or "youtu.be" in query:
                info = ydl.extract_info(query, download=True)
            else:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)['entries'][0]
            
            video_title = info.get('title', 'Audio')
            video_id = info.get('id')
            filename = f"downloads/{video_id}.mp3"

        if os.path.exists(filename):
            if os.path.getsize(filename) > 50 * 1024 * 1024:
                bot.edit_message_text("⚠️ File too large (>50MB)", chat_id, status_msg.message_id)
                os.remove(filename)
                return

            bot.edit_message_text("⬆️ Uploading...", chat_id, status_msg.message_id)
            with open(filename, 'rb') as audio:
                bot.send_audio(chat_id, audio, title=video_title, performer="Bot", caption=f"🎧 {video_title}")
            
            bot.delete_message(chat_id, status_msg.message_id)
            os.remove(filename)
        else:
            bot.edit_message_text("❌ Failed to download", chat_id, status_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", chat_id, status_msg.message_id)

@bot.message_handler(commands=['tr'])
def translate_handler(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3: return bot.reply_to(message, "/tr [lang] [text] (Ex: /tr my Hello)")
    res = translate_text_google(parts[1], parts[2])
    bot.reply_to(message, res)

@bot.message_handler(commands=['say'])
def tts_handler(message):
    parts = message.text.split()
    lang = parts[1] if len(parts) > 1 else 'en'
    text = ""
    
    if message.reply_to_message:
        text = translate_text_google(lang, message.reply_to_message.text)
    elif len(parts) > 2:
        text = " ".join(parts[2:])
    else:
        return bot.reply_to(message, "စာရိုက်ပါ သို့မဟုတ် Reply ထောက်ပါ")

    try:
        tts = gTTS(text=text, lang=lang)
        fn = f"downloads/speak_{message.chat.id}.mp3"
        tts.save(fn)
        with open(fn, 'rb') as audio:
            bot.send_voice(message.chat.id, audio)
        os.remove(fn)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['imagine', 'img'])
def ai_image(message):
    prompt = message.text.replace("/imagine", "").replace("/img", "").strip()
    if not prompt: return bot.reply_to(message, "Prompt ထည့်ပါ")
    
    msg = bot.reply_to(message, "🎨 Generating...")
    seed = random.randint(1, 10000)
    url = f"https://image.pollinations.ai/prompt/{prompt}?seed={seed}&width=1024&height=1024&nologo=true"
    
    try:
        bot.send_photo(message.chat.id, requests.get(url).content, caption=f"🎨 {prompt}")
        bot.delete_message(message.chat.id, msg.message_id)
    except:
        bot.edit_message_text("Error Generating Image", message.chat.id, msg.message_id)

# ==========================================
# 3. FAKE DATA & TOOLS
# ==========================================

@bot.message_handler(commands=['fake'])
def fake_id(message):
    parts = message.text.split()
    country = parts[1].lower() if len(parts) > 1 else 'us'
    fake = fake_jp if country == 'jp' else (fake_th if country == 'th' else fake_us)
    
    txt = f"👤 <b>Fake {country.upper()}</b>\nName: {fake.name()}\nAddr: {fake.address()}\nEmail: {fake.email()}"
    bot.reply_to(message, txt, parse_mode='HTML')

@bot.message_handler(commands=['bin'])
def bin_checker(message):
    # Simple Luhn logic omitted for brevity, adding simple random gen
    bot.reply_to(message, "💳 BIN Gen Logic Executed (Mock).")

# Temp Mail Logic
tm_users = {}
@bot.message_handler(commands=['new'])
def new_mail(message):
    try:
        base = "https://api.mail.tm"
        domain = requests.get(f"{base}/domains").json()['hydra:member'][0]['domain']
        uname = ''.join(random.choices(string.ascii_lowercase, k=8))
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        email = f"{uname}@{domain}"
        
        requests.post(f"{base}/accounts", json={"address": email, "password": pwd})
        token = requests.post(f"{base}/token", json={"address": email, "password": pwd}).json()['token']
        
        tm_users[message.chat.id] = {'token': token, 'email': email}
        bot.reply_to(message, f"📧 Email: <code>{email}</code>\n🔑 Pass: <code>{pwd}</code>", parse_mode='HTML')
    except:
        bot.reply_to(message, "Service Error")

@bot.message_handler(commands=['check'])
def check_mail(message):
    if message.chat.id not in tm_users: return bot.reply_to(message, "/new အရင်လုပ်ပါ")
    token = tm_users[message.chat.id]['token']
    res = requests.get("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {token}"})
    msgs = res.json()['hydra:member']
    if not msgs: return bot.reply_to(message, "📭 Inbox Empty")
    
    txt = ""
    for m in msgs[:5]:
        txt += f"From: {m['from']['address']}\nSubj: {m['subject']}\n\n"
    bot.reply_to(message, txt)

# ==========================================
# 4. AUTO LINK HANDLERS (YouTube, TikTok)
# ==========================================

@bot.message_handler(func=lambda m: is_youtube_url(m.text))
def auto_yt_dl(message):
    # Reuse the logic from smart_mp3_handler by modifying message text internally or calling function
    message.text = f"/mp3 {message.text}"
    smart_mp3_handler(message)

@bot.message_handler(func=lambda m: is_tiktok_url(m.text))
def tiktok_dl(message):
    msg = bot.reply_to(message, "⬇️ TikTok Downloading...")
    try:
        api = "https://www.tikwm.com/api/"
        data = requests.post(api, data={'url': message.text}).json()
        if data['code'] == 0:
            vid_url = data['data']['play']
            desc = data['data']['title']
            bot.send_video(message.chat.id, requests.get(vid_url).content, caption=desc)
            bot.delete_message(message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("❌ Download Failed", message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"Error: {e}", message.chat.id, msg.message_id)

@bot.message_handler(content_types=['photo'])
def photo_to_link(message):
    # Upload to Telegra.ph
    try:
        fid = message.photo[-1].file_id
        fpath = bot.get_file(fid).file_path
        dl = bot.download_file(fpath)
        
        res = requests.post("https://telegra.ph/upload", files={'file': ('img.jpg', dl, 'image/jpeg')}).json()
        if 'src' in res[0]:
            bot.reply_to(message, f"🔗 Link: https://telegra.ph{res[0]['src']}", disable_web_page_preview=True)
    except:
        pass # Ignore errors for random photos

# ==========================================
# RUN
# ==========================================
bot.infinity_polling()
