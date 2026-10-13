import os
import re
import logging
import asyncio
import requests
import yt_dlp
import json
import time
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    constants,
    BotCommand,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= Configuration =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8757608940:AAFpag-wzlorOql2JWs-c2oMu4AP3UPJPPs")
ADMIN_USERNAME = "@vskmm2"
CHANNEL_LINK = "https://t.me/Monkey_D_Luffykh"
WELCOME_BANNER = "https://i.supaimg.com/2c2963a3-a72b-47fd-ba30-ac78827d2091/5138d4bd-41fe-4c79-9c0f-8b3ca4163b1b.jpg"

VIDKRAKEN_API_KEY = "ed47818e-e446-4d4b-9a82-c91ea8f40a42"
POOF_API_KEY = "pk_154739a6534940fa0d26e7de639ea81d"

MEATIKA_API_URL = "https://api.meatika.dev/v1/tts"
MEATIKA_API_KEY = "ck_live_mgGgsfln4gaKHFqid2Lsr7aWes7eI0Pa"

DATA_FILE = "bot_database.json"
WEEK_IN_SECONDS = 7 * 24 * 60 * 60

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ================= Database Functions =================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {"users": {}}
        except Exception as e:
            logging.error(f"Error loading JSON database: {e}")
            return {"users": {}}
    return {"users": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving JSON database: {e}")

def register_or_update_user(user_id, username=""):
    db = load_data()
    user_id = str(user_id)
    current_time = time.time()

    if "users" not in db:
        db["users"] = {}

    if user_id not in db["users"]:
        db["users"][user_id] = {
            "keys": 10,
            "last_reset": current_time,
            "username": username,
            "mode": None,
            "tts_mode": "tts_cute",
            "trans_mode": "km_en"
        }
        save_data(db)
    else:
        if username and db["users"][user_id].get("username") != username:
            db["users"][user_id]["username"] = username
            save_data(db)

    user_info = db["users"][user_id]
    last_reset = user_info.get("last_reset", current_time)
    if current_time - last_reset >= WEEK_IN_SECONDS:
        user_info["keys"] = user_info.get("keys", 0) + 10
        user_info["last_reset"] = current_time
        save_data(db)

    return user_info.get("keys", 0)

def set_user_persistent_state(user_id, key, value):
    db = load_data()
    user_id = str(user_id)
    if "users" in db and user_id in db["users"]:
        db["users"][user_id][key] = value
        save_data(db)

def get_user_persistent_state(user_id, key, default=None):
    db = load_data()
    user_id = str(user_id)
    if "users" in db and user_id in db["users"]:
        return db["users"][user_id].get(key, default)
    return default

# ================= Advanced English Fancy Fonts =================
def custom_translate(text: str, upper_map: str, lower_map: str, digit_map: str = None) -> str:
    res = []
    for ch in text:
        if 'A' <= ch <= 'Z':
            idx = ord(ch) - ord('A')
            res.append(upper_map[idx] if idx < len(upper_map) else ch)
        elif 'a' <= ch <= 'z':
            idx = ord(ch) - ord('a')
            res.append(lower_map[idx] if idx < len(lower_map) else ch)
        elif digit_map and '0' <= ch <= '9':
            idx = ord(ch) - ord('0')
            res.append(digit_map[idx] if idx < len(digit_map) else ch)
        else:
            res.append(ch)
    return "".join(res)

FONT_STYLES = {
    "serif_bold": ("𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙", "𝐚𝐛𝐜𝐝𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝐪𝐫𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣", "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"),
    "sans_bold": ("𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭", "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝚔𝚕𝗺𝚗𝚘𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝚣", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"),
    "italic": ("𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡", "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝚓𝘬𝚕mnop𝘲𝘳𝘴𝘵u𝘝𝘸𝘹𝘺𝘻", "0123456789"),
    "script": ("𝒜ℬ𝒞𝒟ℰℱ𝒢ℋ𝄐𝒥𝒦𝒒ℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵", "𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓿𝓌𝓍𝓎𝓏", "0123456789"),
    "bold_script": ("𝓐𝓑𝐂𝐃𝐄𝐅𝓖𝓗𝐈𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝒰𝓥𝓦𝓧𝓨𝓩", "𝓪𝚋𝓬𝓭𝓮𝚏𝓰𝓱𝑖𝓳𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧", "0123456789"),
    "fraktur": ("𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏Ⓜ𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ", "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷", "0123456789"),
    "double_struck": ("𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ", "𝕒𝕓𝕔𝕕𝕖𝙛𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝓿𝕨𝕩𝕪𝕫", "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"),
    "fullwidth": ("ＡＢＣＤＥＦＧＨＩＪＫＬMNOPQRSTUVWXYZ", "ａｂｃｄｅｆｇｈｉｊ𝚔𝚕ｍ𝚗ｏｐ𝥲ｒｓｔｕｖｗｘｙｚ", "０１２３４５６７８９"),
    "circles": ("ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ", "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ", "⓪①②③④⑤⑥⑦⑧⑨"),
    "monospace": ("𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉", "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣", "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿")
}

def apply_font_style(text: str, style_key: str) -> str:
    if style_key not in FONT_STYLES:
        return text
    um, lm, dm = FONT_STYLES[style_key]
    return custom_translate(text, um, lm, dm)

def build_font_buttons(text: str):
    generated_list = []
    for key in FONT_STYLES.keys():
        generated_list.append(apply_font_style(text, key))
        
    decorations = [
        f"✨ {text} ✨", f"★≡ {text} ≡", f"❤️ {text} ❤️", f"🔥 {text} 🔥",
        f"🎀 {text} 🎀", f"~ {text} ~", f"» {text} «", f"♦ {text} ♦",
        f"【 {text} 】", f"《 {text} 》", f"✿ {text} ✿", f"☽ {text} ☾",
        f"♛ {text} ♛", f"🌈 {text}", f"💎 {text} 💎", f"⚡ {text} ⚡",
        f"📌 {text}", f"🍀 {text} 🍀", f"❄️ {text} ❄️", f"༄{text}࿐"
    ]
    generated_list.extend(decorations)

    keyboard = []
    row = []
    for idx, item in enumerate(generated_list):
        button_text = f"📋 {item[:15]}..." if len(item) > 15 else f"📋 {item}"
        row.append(InlineKeyboardButton(button_text, callback_data=f"copy_f_{idx}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard), generated_list

# ================= Keyboards =================
def get_main_reply_keyboard():
    keyboard = [
        [KeyboardButton("📥 ទាញយកវីដេអូ/MP3"), KeyboardButton("🎙️ ផ្ញើ Voice មកបម្លែង MP3")],
        [KeyboardButton("🎨 Style អក្សរ (Fonts)"), KeyboardButton("✂️ លុប BG")],
        [KeyboardButton("🌐 បង្កើត Xray VPN"), KeyboardButton("🗣️ បម្លែងសំឡេង (TTS)")],
        [KeyboardButton("🌐 បកប្រែភាសា"), KeyboardButton("🚀 បន្ថែម View/Like")],
        [KeyboardButton("📢 ចូលរួម Channel"), KeyboardButton("💬 ទំនាក់ទំនង Admin")],
        [KeyboardButton("🏠 ត្រឡប់ទៅដើមវិញ")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_action_completion_keyboard(mode_name: str):
    keyboard = [
        [InlineKeyboardButton("🔄 ធ្វើមុខងារនេះបន្តទៀត", callback_data="keep_current_mode")],
        [InlineKeyboardButton("🏠 ត្រឡប់ទៅម៉ឺនុយដើម", callback_data="reset_to_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================= Media, Poof.bg & Voice Functions =================
def download_youtube_vidkraken(url: str, is_mp3: bool = False):
    try:
        format_type = "mp3" if is_mp3 else "360"
        submit_url = "https://vidkraken.com/api/v2/download"
        headers = {
            "Authorization": f"Bearer {VIDKRAKEN_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"url": url, "format": format_type}
        
        res = requests.post(submit_url, headers=headers, json=payload, timeout=25)
        data = res.json()
        job_id = data.get("jobId")
        if not job_id:
            return None, None, None

        status_url = f"https://vidkraken.com/api/v2/download/{job_id}"
        download_link = None
        title = "YouTube Video"

        for _ in range(30):
            time.sleep(3)
            status_res = requests.get(status_url, headers=headers, timeout=15)
            status_data = status_res.json()
            if status_data.get("status") == "COMPLETED":
                download_link = status_data.get("downloadUrl")
                title = status_data.get("title", title)
                break
            elif status_data.get("status") == "FAILED":
                break

        if download_link:
            file_extension = "mp3" if is_mp3 else "mp4"
            file_path = f"downloads/youtube_{int(time.time())}.{file_extension}"
            
            file_req = requests.get(download_link, stream=True, timeout=60)
            with open(file_path, 'wb') as f:
                for chunk in file_req.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return file_path, title, download_link
    except Exception as e:
        logging.error(f"VidKraken Download Error: {e}")
    return None, None, None

def download_media_file(url: str, is_mp3: bool = False):
    if "youtube.com" in url or "youtu.be" in url:
        return download_youtube_vidkraken(url, is_mp3)

    ydl_opts = {
        'outtmpl': 'downloads/%(id)s_%(epoch)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    if is_mp3:
        ydl_opts.update({'format': 'bestaudio/best'})
    else:
        ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Downloaded Media')
            direct_url = info.get('url', url)
            return filename, title, direct_url
    except Exception as e:
        logging.error(f"yt-dlp Error: {e}")
        return None, None, None

def remove_background(image_path: str) -> str:
    try:
        output_path = image_path.replace(".", "_nobg.")
        url = "https://api.poof.bg/v1/remove"
        headers = {
            "x-api-key": POOF_API_KEY
        }
        
        with open(image_path, 'rb') as f:
            files = {
                'image_file': (os.path.basename(image_path), f, 'image/jpeg')
            }
            response = requests.post(url, headers=headers, files=files, timeout=30)
            
        if response.status_code == 200:
            with open(output_path, 'wb') as out:
                out.write(response.content)
            return output_path
        else:
            logging.error(f"Poof.bg API Error: {response.text}")
    except Exception as e:
        logging.error(f"Poof.bg Exception: {e}")
    return None

def generate_tts_voice(text: str, user_id: str, tts_mode: str = "tts_cute") -> str:
    try:
        audio_path = f"downloads/voice_{user_id}_{int(time.time())}.mp3"
        
        if tts_mode == "tts_Loveណាចា":
            headers = {
                "Authorization": f"Bearer {MEATIKA_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {"text": text, "voice_model": "Loveណាចា"}
            response = requests.post(MEATIKA_API_URL, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                return audio_path

        speed_param = "&ttsspeed=1.2" if tts_mode == "tts_cute" else "&ttsspeed=1"
        encoded_text = requests.utils.quote(text)
        voice_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl=km&client=tw-ob{speed_param}"
        
        res = requests.get(voice_url, timeout=15)
        if res.status_code == 200:
            raw_path = f"downloads/raw_{user_id}_{int(time.time())}.mp3"
            with open(raw_path, "wb") as f:
                f.write(res.content)
            
            if tts_mode == "tts_cute":
                cmd = f'ffmpeg -i "{raw_path}" -filter:a "rubberband=pitch=1.35" "{audio_path}" -y'
                os.system(cmd)
                if os.path.exists(raw_path):
                    os.remove(raw_path)
                if os.path.exists(audio_path):
                    return audio_path
            return raw_path
    except Exception as e:
        logging.error(f"TTS Error: {e}")
    return None

# ================= Commands =================
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "ចាប់ផ្តើមប្រើប្រាស់ Bot"),
        BotCommand("style", "បង្កើត Style អក្សរស្អាតៗ"),
        BotCommand("removebg", "មុខងារលុបផ្ទៃខាងក្រោយរូបភាព"),
        BotCommand("tts", "បម្លែងអក្សរទៅជាសំឡេង Voice Cute"),
        BotCommand("translate", "បកប្រែភាសា"),
        BotCommand("help", "របៀបប្រើប្រាស់ Bot")
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.TYPING)
        user = update.message.from_user
        user_id = user.id
        username = f"@{user.username}" if user.username else user.first_name
        
        register_or_update_user(user_id, username)
        set_user_persistent_state(user_id, "mode", None)
        
        welcome_text = (
            "👋 **ស្វាគមន៍មកកាន់ All-in-One Multi-Bot!**\n\n"
            "✨ **មុខងារពិសេស:**\n"
            "📥 ទាញយកវីដេអូ/MP3 & ផ្ញើ Voice មកវាយពាក្យ MP3\n"
            "🎨 បង្កើត Style អក្សរ (Fancy Fonts) ស្អាតៗជាច្រើន\n"
            "✂️ លុបផ្ទៃខាងក្រោយរូបភាព (Poof.bg API)\n"
            "🌐 បង្កើត Xray VPN (Free 10 Key រៀងរាល់ ១ សប្ដាហ៍)\n"
            "🗣️ បម្លែងអក្សរទៅជាសំឡេងបែប **Cute/ខ្ជូតៗ 🎀**\n"
            "🌐 បកប្រែភាសា និងសេវាកម្មផ្សេងៗ\n\n"
            "👇 **សូមចុចលើប៊ូតុងម៉ឺនុយខាងក្រោម ឬផ្ញើ Link/File/Voice មកទីនេះ៖**"
        )

        try:
            await update.message.reply_photo(
                photo=WELCOME_BANNER,
                caption=welcome_text,
                reply_markup=get_main_reply_keyboard(),
                parse_mode="Markdown"
            )
        except Exception:
            await update.message.reply_text(welcome_text, reply_markup=get_main_reply_keyboard(), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Start command error: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **របៀបប្រើប្រាស់ Bot:**\n\n"
        "1. **📥 ទាញយកវីដេអូ/MP3:** ផ្ញើ Link (TikTok, YouTube, FB...) មកកាន់ Bot ផ្ទាល់។\n"
        "2. **🎙️ បម្លែង Voice ➔ MP3:** ផ្ញើសំឡេង Voice មក រួចវាយពាក្យ **MP3** Bot នឹងបម្លែងជូនភ្លាម។\n"
        "3. **🎨 Style អក្សរ:** ចុចប៊ូតុង '🎨 Style អក្សរ' រួចផ្ញើអត្ថបទដើម្បី Copy Font ស្អាតៗ។\n"
        "4. **✂️ លុប BG:** ចុចប៊ូតុង '✂️ លុប BG' រួចផ្ញើរូបភាពមក។"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_main_reply_keyboard())

async def removebg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_persistent_state(update.message.from_user.id, "mode", "remove_bg")
    await update.message.reply_text("✂️ **ចូលកាន់មុខងារលុបផ្ទៃខាងក្រោយ**\nសូមផ្ញើរូបភាពរបស់អ្នកមកទីនេះ!", parse_mode="Markdown", reply_markup=get_main_reply_keyboard())

async def tts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_persistent_state(update.message.from_user.id, "mode", "tts")
    tts_kb = [
        [InlineKeyboardButton("🎀 សំឡេង Cute/ខ្ជូតៗ (Default)", callback_data="tts_cute")],
        [InlineKeyboardButton("🌸 សំឡេង Loveណាចា", callback_data="tts_Loveណាចា")],
        [InlineKeyboardButton("👩 សំឡេងស្រី ធម្មតា", callback_data="tts_ស្រី_ធម្មតា"), InlineKeyboardButton("👨 សំឡេងប្រុស ធម្មតា", callback_data="tts_ប្រុស_ធម្មតា")]
    ]
    await update.message.reply_text("🗣️ **សូមជ្រើសរើសប្រភេទសំឡេងដែលអ្នកចូលចិត្ត៖**", reply_markup=InlineKeyboardMarkup(tts_kb), parse_mode="Markdown")

async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_persistent_state(update.message.from_user.id, "mode", "translate")
    trans_keyboard = [
        [InlineKeyboardButton("🇰🇭 ខ្មែរ ➔ 🇬🇧 អង់គ្លេស", callback_data="set_tr_km_en"), InlineKeyboardButton("🇬🇧 អង់គ្លេស ➔ 🇰🇭 ខ្មែរ", callback_data="set_tr_en_km")],
        [InlineKeyboardButton("🇰🇭 ខ្មែរ ➔ 🇨🇳 ចិន", callback_data="set_tr_km_zh-CN"), InlineKeyboardButton("🇨🇳 ចិន ➔ 🇰🇭 ខ្មែរ", callback_data="set_tr_zh-CN_km")]
    ]
    await update.message.reply_text("🌐 **សូមជ្រើសរើសទិសដៅនៃការបកប្រែ៖**", reply_markup=InlineKeyboardMarkup(trans_keyboard), parse_mode="Markdown")

# ================= Callback Handler =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "reset_to_home":
        set_user_persistent_state(user_id, "mode", None)
        await query.message.reply_text("🏠 **បានត្រឡប់មកកាន់ម៉ឺនុយដើមវិញហើយ!**", reply_markup=get_main_reply_keyboard())
        return

    elif data == "keep_current_mode":
        await query.message.reply_text("👌 អ្នកអាចផ្ញើអត្ថបទ ឬ File ដើម្បីធ្វើមុខងារនេះបន្តទៀតបាន!")
        return

    elif data == "convert_voice_to_mp3":
        voice_file_id = context.user_data.get('last_voice_file_id')
        if not voice_file_id:
            await query.message.reply_text("❌ រកមិនឃើញសំឡេង Voice ទេ។ សូមផ្ញើសំឡេង Voice ម្ដងទៀត។")
            return
        await process_and_send_voice_mp3(query.message, context, voice_file_id, user_id)
        return

    elif data.startswith("copy_f_"):
        idx = int(data.replace("copy_f_", ""))
        cached_styles = context.user_data.get('cached_styles', [])
        
        if idx < len(cached_styles):
            copied_text = cached_styles[idx]
            await query.answer("✅ បានជ្រើសរើស!", show_alert=False)
            await query.message.reply_text(
                f"📋 **អត្ថបទរបស់អ្នក (ចុចលើអត្ថបទខាងក្រោមដើម្បី Copy):**\n\n`{copied_text}`",
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ អស់សុពលភាព! សូមផ្ញើឈ្មោះម្តងទៀត។", show_alert=True)
        return

    elif data in ["dl_mp4", "dl_mp3"]:
        target_url = context.user_data.get('download_url')
        if not target_url:
            await query.message.reply_text("❌ រកមិនឃើញ Link ឡើយ! សូមផ្ញើ Link ម្ដងទៀត។")
            return

        is_mp3 = (data == "dl_mp3")
        status_msg = await query.message.reply_text("⏳ កំពុងដំណើរការទាញយក File...")
        
        action = constants.ChatAction.UPLOAD_VOICE if is_mp3 else constants.ChatAction.UPLOAD_VIDEO
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action=action)

        file_path, title, direct_url = await asyncio.to_thread(download_media_file, target_url, is_mp3)

        if file_path and os.path.exists(file_path):
            caption = f"✅ **ទាញយកជោគជ័យ!**\n📌 {title if title else ''}"
            try:
                with open(file_path, 'rb') as file:
                    if is_mp3:
                        await query.message.reply_audio(audio=file, caption=caption, parse_mode="Markdown")
                    else:
                        await query.message.reply_video(video=file, caption=caption, parse_mode="Markdown")
                
                await query.message.reply_text("✨ **តើអ្នកចង់ធ្វើអ្វីបន្តទៀត?**", reply_markup=get_action_completion_keyboard("ទាញយក Media"))
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            await query.message.reply_text("❌ មិនអាចទាញយក Media ពី Link នេះបានទេ!")

        try:
            await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
        except Exception:
            pass

    elif data.startswith("tts_"):
        set_user_persistent_state(user_id, "tts_mode", data)
        set_user_persistent_state(user_id, "mode", "tts")
        mode_name = "Cute/ខ្ជូតៗ 🎀" if data == "tts_cute" else data.replace("tts_", "").replace("_", " ")
        await query.message.reply_text(f"✅ បានកំណត់សំឡេង៖ **{mode_name}**\n\nឥឡូវនេះអ្នកអាចផ្ញើសារអត្ថបទមកដើម្បីទទួលបាន Voice Note ស្អាតៗ!", parse_mode="Markdown")

    elif data.startswith("set_tr_"):
        mode_val = data.replace("set_tr_", "")
        set_user_persistent_state(user_id, "trans_mode", mode_val)
        set_user_persistent_state(user_id, "mode", "translate")
        await query.message.reply_text("✅ បានកំណត់ទិសដៅបកប្រែជោគជ័យ!\n\nឥឡូវនេះអ្នកអាចផ្ញើសារដើម្បីបកប្រែបានភ្លាមៗ។")

# ================= Photo Handler =================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    current_mode = get_user_persistent_state(user_id, "mode")
    
    if current_mode == 'remove_bg':
        status_msg = await update.message.reply_text("⏳ កំពុងដំណើរការ...")
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.UPLOAD_PHOTO)
        
        photo_file = await update.message.photo[-1].get_file()
        input_path = f"downloads/{user_id}_{int(time.time())}.jpg"
        await photo_file.download_to_drive(input_path)

        output_path = await asyncio.to_thread(remove_background, input_path)

        if output_path and os.path.exists(output_path):
            await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.UPLOAD_DOCUMENT)
            with open(output_path, 'rb') as f:
                await update.message.reply_document(
                    document=f, 
                    filename="removed_background.png",
                    caption="✨ **លុបផ្ទៃខាងក្រោយជោគជ័យ!**", 
                    parse_mode="Markdown"
                )
            if os.path.exists(output_path):
                os.remove(output_path)
            
            await update.message.reply_text("✨ **តើអ្នកចង់ធ្វើអ្វីបន្តទៀត?**", reply_markup=get_action_completion_keyboard("លុប BG"))
        else:
            await update.message.reply_text("❌ មិនអាចលុបផ្ទៃខាងក្រោយបានទេ!")

        if os.path.exists(input_path):
            os.remove(input_path)
        
        try:
            await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
        except Exception:
            pass
    else:
        await update.message.reply_text("📸 សូមចុចជ្រើសរើសមុខងារ **✂️ លុប BG** ពីម៉ឺនុយជាមុនសិន!")

# ================= Helper to Process Voice to MP3 =================
async def process_and_send_voice_mp3(message, context, voice_file_id, user_id):
    status_msg = await message.reply_text("⏳ កំពុងបម្លែង Voice ទៅជា MP3...")
    await context.bot.send_chat_action(chat_id=message.chat_id, action=constants.ChatAction.UPLOAD_AUDIO)

    timestamp = int(time.time())
    input_voice_path = f"downloads/voice_{user_id}_{timestamp}.oga"
    output_mp3_path = f"downloads/imsela_{int(time.time())%10000}.mp3"

    try:
        tg_file = await context.bot.get_file(voice_file_id)
        await tg_file.download_to_drive(input_voice_path)

        cmd = f'ffmpeg -i "{input_voice_path}" -codec:a libmp3lame -qscale:a 2 "{output_mp3_path}" -y'
        ret = os.system(cmd)

        if ret == 0 and os.path.exists(output_mp3_path):
            with open(output_mp3_path, 'rb') as audio_f:
                await message.reply_audio(
                    audio=audio_f,
                    title=os.path.basename(output_mp3_path),
                    performer="មិនស្គាល់សិល្បករ",
                    caption="🎵 **បម្លែង Voice ទៅជា MP3 រួចរាល់!**",
                    parse_mode="Markdown"
                )
            await message.reply_text("✨ **តើអ្នកចង់ធ្វើអ្វីបន្តទៀត?**", reply_markup=get_action_completion_keyboard("បម្លែង Voice ជា MP3"))
        else:
            await message.reply_text("❌ បម្លែងមិនបានទេ!")
    except Exception as e:
        logging.error(f"Voice to MP3 Error: {e}")
        await message.reply_text("⚠️ មានបញ្ហាក្នុងការបម្លែង Voice!")
    finally:
        if os.path.exists(input_voice_path):
            os.remove(input_voice_path)
        if os.path.exists(output_mp3_path):
            os.remove(output_mp3_path)
        try:
            await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
        except Exception:
            pass

# ================= Telegram Voice Handler =================
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    voice = message.voice

    if voice:
        # រក្សាទុក Voice file_id ទុកក្នុង user_data របស់អ្នកប្រើប្រាស់
        context.user_data['last_voice_file_id'] = voice.file_id
        await message.reply_text(
            "🎙️ **រកឃើញសំឡេង Voice Note ហើយ!**\n"
            "👉 សូមវាយពាក្យ **`MP3`** ឬចុចប៊ូតុងខាងក្រោមដើម្បីបម្លែងជាፋ៊ីល MP3៖",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 បម្លែងជា MP3 ភ្លាម", callback_data="convert_voice_to_mp3")]
            ]),
            parse_mode="Markdown"
        )

# ================= Text Message Handler =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
        
    user = update.message.from_user
    user_id = str(user.id)
    username = f"@{user.username}" if user.username else "គ្មាន (No Username)"
    register_or_update_user(user_id, username)

    # ត្រួតពិនិត្យប្រសិនបើអ្នកប្រើប្រាស់វាយពាក្យ "MP3"
    if text.strip().upper() == "MP3":
        voice_file_id = context.user_data.get('last_voice_file_id')
        if not voice_file_id:
            await update.message.reply_text("❌ សូមផ្ញើសំឡេង Voice Note ចូលមកសិន ទើបអាចវាយពាក្យ MP3 បម្លែងបាន!")
            return
        await process_and_send_voice_mp3(update.message, context, voice_file_id, user_id)
        return

    if text == "🏠 ត្រឡប់ទៅដើមវិញ":
        set_user_persistent_state(user_id, "mode", None)
        await update.message.reply_text(
            "🏠 **បានត្រឡប់មករកម៉ឺនុយដើមវិញហើយ!**\nសូមជ្រើសរើសមុខងារដែលអ្នកចង់ប្រើប្រាស់បន្ត៖",
            reply_markup=get_main_reply_keyboard(),
            parse_mode="Markdown"
        )
        return

    if text == "📥 ទាញយកវីដេអូ/MP3":
        set_user_persistent_state(user_id, "mode", "download")
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.TYPING)
        await update.message.reply_text("📥 **ទម្រង់ទាញយក៖**\nសូមផ្ញើ Link វីដេអូចូលមកទីនេះ។", parse_mode="Markdown")
        return

    elif text == "🎙️ ផ្ញើ Voice មកបម្លែង MP3":
        set_user_persistent_state(user_id, "mode", "voice_mp3")
        await update.message.reply_text(
            "🎙️ **មុខងារបម្លែង Voice ➔ MP3**\n\n"
            "សូមផ្ញើសំឡេង Voice Note ចូលមកទីនេះ រួចវាយពាក្យ **`MP3`** ដើម្បីបម្លែង!",
            parse_mode="Markdown"
        )
        return

    elif text == "🎨 Style អក្សរ (Fonts)":
        set_user_persistent_state(user_id, "mode", "font_style")
        await update.message.reply_text(
            "🎨 **ចូលកាន់មុខងារបង្កើត Style អក្សរ (Fancy Fonts)**\n\n"
            "សូមផ្ញើឈ្មោះ ឬអត្ថបទអង់គ្លេសរបស់អ្នកមកទីនេះ!",
            parse_mode="Markdown"
        )
        return

    elif text == "✂️ លុប BG":
        set_user_persistent_state(user_id, "mode", "remove_bg")
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.TYPING)
        await update.message.reply_text("✂️ **ចូលកាន់មុខងារលុបផ្ទៃខាងក្រោយ**\nសូមផ្ញើរូបភាពរបស់អ្នកមកទីនេះ!", parse_mode="Markdown")
        return

    elif text == "🗣️ បម្លែងសំឡេង (TTS)":
        set_user_persistent_state(user_id, "mode", "tts")
        tts_kb = [
            [InlineKeyboardButton("🎀 សំឡេង Cute/ខ្ជូតៗ (Default)", callback_data="tts_cute")],
            [InlineKeyboardButton("🌸 សំឡេង Loveណាចា", callback_data="tts_Loveណាចា")],
            [InlineKeyboardButton("👩 សំឡេងស្រី ធម្មតា", callback_data="tts_ស្រី_ធម្មតា"), InlineKeyboardButton("👨 សំឡេងប្រុស ធម្មតា", callback_data="tts_ប្រុស_ធម្មតា")]
        ]
        await update.message.reply_text("🗣️ **សូមជ្រើសរើសប្រភេទសំឡេង៖**", reply_markup=InlineKeyboardMarkup(tts_kb), parse_mode="Markdown")
        return

    elif text == "🌐 បកប្រែភាសា":
        set_user_persistent_state(user_id, "mode", "translate")
        trans_keyboard = [
            [InlineKeyboardButton("🇰🇭 ខ្មែរ ➔ 🇬🇧 អង់គ្លេស", callback_data="set_tr_km_en"), InlineKeyboardButton("🇬🇧 អង់គ្លេស ➔ 🇰🇭 ខ្មែរ", callback_data="set_tr_en_km")],
            [InlineKeyboardButton("🇰🇭 ខ្មែរ ➔ 🇨🇳 ចិន", callback_data="set_tr_km_zh-CN"), InlineKeyboardButton("🇨🇳 ចិន ➔ 🇰🇭 ខ្មែរ", callback_data="set_tr_zh-CN_km")]
        ]
        await update.message.reply_text("🌐 **សូមជ្រើសរើសទិសដៅនៃការបកប្រែ៖**", reply_markup=InlineKeyboardMarkup(trans_keyboard), parse_mode="Markdown")
        return

    mode = get_user_persistent_state(user_id, "mode")

    if mode == 'tts':
        tts_mode = get_user_persistent_state(user_id, "tts_mode", "tts_cute")
        status_msg = await update.message.reply_text("⏳ កំពុងបង្កើត Voice Note សំឡេង Cute... 🎀")
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.RECORD_VOICE)
        
        audio_path = await asyncio.to_thread(generate_tts_voice, text, str(user_id), tts_mode)

        if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 100:
            await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.UPLOAD_VOICE)
            with open(audio_path, "rb") as voice_file:
                await update.message.reply_voice(voice=voice_file, caption="🎀 **សំឡេង Cute របស់អ្នករួចរាល់ហើយ!**")
            os.remove(audio_path)
            
            await update.message.reply_text("✨ **តើអ្នកចង់ធ្វើអ្វីបន្តទៀត?**", reply_markup=get_action_completion_keyboard("បម្លែងសំឡេង"))
        else:
            await update.message.reply_text("⚠️ មិនអាចបង្កើតសំឡេងបានទេ!")

        try:
            await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
        except Exception:
            pass
        return

    if mode == 'font_style':
        inline_kb, styles_list = build_font_buttons(text)
        context.user_data['cached_styles'] = styles_list

        await update.message.reply_text(
            f"✨ **លទ្ធផល Style អក្សរសម្រាប់៖** `{text}`\nសូមចុចលើប៊ូតុងខាងក្រោមដើម្បី Copy!",
            reply_markup=inline_kb,
            parse_mode="Markdown"
        )
        await update.message.reply_text("✨ **តើអ្នកចង់ធ្វើអ្វីបន្តទៀត?**", reply_markup=get_action_completion_keyboard("Style អក្សរ"))
        return

    if mode == 'translate':
        trans_mode = get_user_persistent_state(user_id, "trans_mode", "km_en")
        src_lang, dest_lang = trans_mode.split('_')
        status_msg = await update.message.reply_text("⏳ កំពុងដំណើរការ...")
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.TYPING)
        
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_lang}&tl={dest_lang}&dt=t&q={requests.utils.quote(text)}"
            res = requests.get(url, timeout=10).json()
            translated_text = "".join([item[0] for item in res[0] if item[0]])
            await update.message.reply_text(f"🌐 **លទ្ធផលបកប្រែ:**\n`{translated_text}`", parse_mode="Markdown")
            await update.message.reply_text("✨ **តើអ្នកចង់ធ្វើអ្វីបន្តទៀត?**", reply_markup=get_action_completion_keyboard("បកប្រែភាសា"))
        except Exception as e:
            await update.message.reply_text("⚠️ មានបញ្ហា!")
        finally:
            try:
                await context.bot.delete_message(chat_id=status_msg.chat_id, message_id=status_msg.message_id)
            except Exception:
                pass
        return

    url_match = re.search(r'https?://[^\s]+', text)
    if url_match:
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=constants.ChatAction.TYPING)
        target_url = url_match.group(0)
        context.user_data['download_url'] = target_url
        keyboard = [
            [
                InlineKeyboardButton("🎬 MP4 (Video)", callback_data="dl_mp4"),
                InlineKeyboardButton("🎵 MP3 (Audio)", callback_data="dl_mp3"),
            ]
        ]
        await update.message.reply_text(
            "🎬 **រកឃើញ Link Media!**\nតើអ្នកចង់ទាញយកជាទម្រង់មួយណា?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "💡 **សូមជ្រើសរើសមុខងារពី Menu ខាងក្រោម!**",
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )

# ================= Execution =================
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(set_bot_commands).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("removebg", removebg_command))
    app.add_handler(CommandHandler("tts", tts_command))
    app.add_handler(CommandHandler("translate", translate_command))
    app.add_handler(CommandHandler("help", help_command))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot កំពុងដំណើរការយ៉ាងរលូន...")
    app.run_polling()
