import os, sys, re, sqlite3, datetime, time
import requests as http_requests
from threading import Thread

from flask import Flask, request as flask_req
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommand, BotCommandScopeDefault
import openpyxl

# ════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════
API_ID      = 30334076
API_HASH    = '59792fbc49ed08135f985c6c312c9b52'
BOT_TOKEN   = '8667327104:AAE7jXGGk9iDOq6tDZefviRRHUWXaIIG00g'
SUPER_ADMIN = 8890678382
OTP_GROUP   = -1004355081956
BOT_FILE    = os.path.abspath(__file__)

FORCE_SUBS = {
    "UnlimitedWSMethod0":  "📢 Channel 1",
    "QueenIraMoniBithiBD": "📢 Channel 2",
    "QueenIraMoniBithi_BD":"💬 Group 1",
    "unlimited_ws_method": "💬 Group 2",
    "Tareq_SMS_Pro_OTP":   "🔥 OTP Group",
}

SVC = {
    "whatsapp":"💬 WhatsApp","telegram":"🔹 Telegram","tiktok":"🎵 TikTok",
    "facebook":"🌐 Facebook","instagram":"📸 Instagram",
}

COUNTRIES = [
    ("Afghanistan","af","🇦🇫"),("Albania","al","🇦🇱"),("Algeria","dz","🇩🇿"),
    ("Angola","ao","🇦🇴"),("Argentina","ar","🇦🇷"),("Armenia","am","🇦🇲"),
    ("Australia","au","🇦🇺"),("Austria","at","🇦🇹"),("Azerbaijan","az","🇦🇿"),
    ("Bahrain","bh","🇧🇭"),("Bangladesh","bd","🇧🇩"),("Belarus","by","🇧🇾"),
    ("Belgium","be","🇧🇪"),("Bolivia","bo","🇧🇴"),("Brazil","br","🇧🇷"),
    ("Bulgaria","bg","🇧🇬"),("Burundi","bi","🇧🇮"),("Cambodia","kh","🇰🇭"),
    ("Cameroon","cm","🇨🇲"),("Canada","ca","🇨🇦"),("Chad","td","🇹🇩"),
    ("Chile","cl","🇨🇱"),("China","cn","🇨🇳"),("Colombia","co","🇨🇴"),
    ("Congo","cg","🇨🇬"),("Costa Rica","cr","🇨🇷"),("Croatia","hr","🇭🇷"),
    ("Cuba","cu","🇨🇺"),("Czech Republic","cz","🇨🇿"),("DR Congo","cd","🇨🇩"),
    ("Denmark","dk","🇩🇰"),("Dominican Rep","do","🇩🇴"),("Ecuador","ec","🇪🇨"),
    ("Egypt","eg","🇪🇬"),("El Salvador","sv","🇸🇻"),("Ethiopia","et","🇪🇹"),
    ("Finland","fi","🇫🇮"),("France","fr","🇫🇷"),("Germany","de","🇩🇪"),
    ("Ghana","gh","🇬🇭"),("Greece","gr","🇬🇷"),("Guatemala","gt","🇬🇹"),
    ("Guinea","gn","🇬🇳"),("Honduras","hn","🇭🇳"),("Hungary","hu","🇭🇺"),
    ("India","in","🇮🇳"),("Indonesia","id","🇮🇩"),("Iran","ir","🇮🇷"),
    ("Iraq","iq","🇮🇶"),("Ireland","ie","🇮🇪"),("Israel","il","🇮🇱"),
    ("Italy","it","🇮🇹"),("Jamaica","jm","🇯🇲"),("Japan","jp","🇯🇵"),
    ("Jordan","jo","🇯🇴"),("Kazakhstan","kz","🇰🇿"),("Kenya","ke","🇰🇪"),
    ("Kuwait","kw","🇰🇼"),("Kyrgyzstan","kg","🇰🇬"),("Laos","la","🇱🇦"),
    ("Lebanon","lb","🇱🇧"),("Libya","ly","🇱🇾"),("Madagascar","mg","🇲🇬"),
    ("Malawi","mw","🇲🇼"),("Malaysia","my","🇲🇾"),("Mali","ml","🇲🇱"),
    ("Mexico","mx","🇲🇽"),("Moldova","md","🇲🇩"),("Mongolia","mn","🇲🇳"),
    ("Morocco","ma","🇲🇦"),("Mozambique","mz","🇲🇿"),("Myanmar","mm","🇲🇲"),
    ("Nepal","np","🇳🇵"),("Netherlands","nl","🇳🇱"),("New Zealand","nz","🇳🇿"),
    ("Nicaragua","ni","🇳🇮"),("Niger","ne","🇳🇪"),("Nigeria","ng","🇳🇬"),
    ("Norway","no","🇳🇴"),("Oman","om","🇴🇲"),("Pakistan","pk","🇵🇰"),
    ("Palestine","ps","🇵🇸"),("Panama","pa","🇵🇦"),("Paraguay","py","🇵🇾"),
    ("Peru","pe","🇵🇪"),("Philippines","ph","🇵🇭"),("Poland","pl","🇵🇱"),
    ("Portugal","pt","🇵🇹"),("Qatar","qa","🇶🇦"),("Romania","ro","🇷🇴"),
    ("Russia","ru","🇷🇺"),("Rwanda","rw","🇷🇼"),("Saudi Arabia","sa","🇸🇦"),
    ("Senegal","sn","🇸🇳"),("Serbia","rs","🇷🇸"),("Sierra Leone","sl","🇸🇱"),
    ("Somalia","so","🇸🇴"),("South Africa","za","🇿🇦"),("South Korea","kr","🇰🇷"),
    ("Spain","es","🇪🇸"),("Sri Lanka","lk","🇱🇰"),("Sudan","sd","🇸🇩"),
    ("Sweden","se","🇸🇪"),("Switzerland","ch","🇨🇭"),("Syria","sy","🇸🇾"),
    ("Taiwan","tw","🇹🇼"),("Tajikistan","tj","🇹🇯"),("Tanzania","tz","🇹🇿"),
    ("Thailand","th","🇹🇭"),("Togo","tg","🇹🇬"),("Tunisia","tn","🇹🇳"),
    ("Turkey","tr","🇹🇷"),("Turkmenistan","tm","🇹🇲"),("Uganda","ug","🇺🇬"),
    ("Ukraine","ua","🇺🇦"),("UAE","ae","🇦🇪"),("UK","uk","🇬🇧"),
    ("USA","us","🇺🇸"),("Uruguay","uy","🇺🇾"),("Uzbekistan","uz","🇺🇿"),
    ("Venezuela","ve","🇻🇪"),("Vietnam","vn","🇻🇳"),("Yemen","ye","🇾🇪"),
    ("Zambia","zm","🇿🇲"),("Zimbabwe","zw","🇿🇼"),
]
COUNTRY_MAP = {s: (n, f) for n, s, f in COUNTRIES}

# ════════════════════════════════════════════════════════════
#  GORGEOUS UI HELPERS
# ════════════════════════════════════════════════════════════
def HDR(title: str, icon: str = "🚀") -> str:
    """Professional header for every message"""
    line = "━" * 28
    return f"{line}\n{icon}  **{title}**\n{line}\n"

def FTR(extra: str = "") -> str:
    """Professional footer"""
    base = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
    return base + (f"\n{extra}" if extra else "")

def STATUS(val, good_thresh=1):
    """Color-coded status"""
    if isinstance(val, int):
        if val >= good_thresh: return f"✅ **{val}**"
        return f"❌ **{val}**"
    return f"✅ {val}" if val else f"❌ N/A"

def PROG(done: int, total: int, width: int = 10) -> str:
    """Progress bar: ████████░░ 8/10"""
    if total == 0: return "░" * width + " 0/0"
    filled = round(done / total * width)
    return "█" * filled + "░" * (width - filled) + f" {done}/{total}"

def DIVIDER() -> str:
    return "\n┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"



# ════════════════════════════════════════════════════════════
#  FLASK keep-alive + OTP webhook
# ════════════════════════════════════════════════════════════
flask_app = Flask('')

def mask_number(phone: str) -> str:
    """Insert XX before the last 3 digits: +258872746205 → +258872746XX205"""
    prefix = '+' if phone.startswith('+') else ''
    digits = re.sub(r'[^\d]', '', phone)
    if len(digits) <= 3:
        return phone
    return prefix + digits[:-3] + 'XX' + digits[-3:]

@flask_app.route('/')
def home(): return "✅ Tareq SMS Pro is running!"

@flask_app.route('/alive')
def alive(): return "OK", 200

@flask_app.route('/webhook/otp', methods=['GET','POST'])
def otp_hook():
    try:
        d = (flask_req.get_json(silent=True) or flask_req.form
             if flask_req.method=='POST' else flask_req.args)
        raw_msg = (d.get('sms') or d.get('message') or d.get('text') or '').strip()
        phone   = (d.get('phone') or d.get('number') or d.get('sim') or '').strip()
        sender  = (d.get('sender') or d.get('app') or d.get('from') or 'Unknown').strip()
        if not raw_msg: return "no msg", 400

        now  = str(datetime.datetime.now())
        norm = re.sub(r'[^\d]', '', phone)

        c.execute("INSERT INTO otp_log(phone,sender,received_at) VALUES(?,?,?)",
                  (phone, sender, now))

        c.execute(
            "SELECT user_id FROM user_number_assignments "
            "WHERE REPLACE(REPLACE(number,'+',''),'-','')=?", (norm,))
        owner_row = c.fetchone()
        uid_owner = owner_row[0] if owner_row else None

        c.execute(
            "SELECT country, service FROM premium_stock "
            "WHERE REPLACE(REPLACE(number,'+',''),'-','')=?", (norm,))
        stock_row = c.fetchone()
        country_short = stock_row[0] if stock_row else ''
        service_key   = stock_row[1] if stock_row else ''

        country_name = 'Unknown'
        country_flag = '🌍'
        if country_short:
            info = COUNTRY_MAP.get(country_short)
            if info:
                country_name, country_flag = info[0], info[1]

        svc_name = SVC.get(service_key, service_key.upper() if service_key else 'Unknown')
        masked   = mask_number(phone)
        tg_url   = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        if uid_owner:
            td = str(datetime.date.today())
            c.execute("SELECT otp_count FROM history WHERE user_id=? AND date=?", (uid_owner, td))
            h = c.fetchone()
            if h: c.execute("UPDATE history SET otp_count=otp_count+1 WHERE user_id=? AND date=?",
                            (uid_owner, td))
            else: c.execute("INSERT INTO history VALUES(?,?,1,0)", (uid_owner, td))

            priv_txt = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉  *নতুন OTP এসেছে!*  🎉\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌐 *দেশ:*    {country_flag} {country_name}\n"
                f"📱 *নাম্বার:* `{phone}`\n"
                f"🚨 *সার্ভিস:* {svc_name}\n"
                f"🏢 *সেন্ডার:* {sender}\n\n"
                f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
                f"🔐 *আপনার OTP কোড:*\n\n"
                f"╔══════════════════════╗\n"
                f"║  💬  `{raw_msg}`  ║\n"
                f"╚══════════════════════╝\n\n"
                f"⚡ দ্রুত ব্যবহার করুন!\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
            )
            try:
                http_requests.post(tg_url, json={
                    "chat_id": uid_owner,
                    "text": priv_txt,
                    "parse_mode": "Markdown"
                }, timeout=5)
            except: pass

        db.commit()

        comm_link = glink('support_group', 'https://t.me')
        group_txt = (
            f"🚀 *ROCKET OTP BOT* 🚀\n\n"
            f"🎉 *NEW OTP RECEIVED* 🎉\n\n"
            f"🌐 *Country:* {country_flag} {country_name}\n"
            f"📱 *Number:* `{masked}`\n"
            f"🚨 *Service:* {svc_name}\n"
            f"💬 *OTP:* `{raw_msg}`"
        )
        group_kbd = {"inline_keyboard": [[
            {"text": "🚀 Community", "url": comm_link},
            {"text": "🗄 Number",    "url": f"https://t.me/{BOT_TOKEN.split(':')[0]}"}
        ]]}

        try:
            http_requests.post(tg_url, json={
                "chat_id": OTP_GROUP,
                "text": group_txt,
                "parse_mode": "Markdown",
                "reply_markup": group_kbd
            }, timeout=5)
        except: pass

        admin_txt = (
            f"📥 *Admin OTP Alert*\n"
            f"📱 `{phone}` → {country_flag} {country_name} | {svc_name}\n"
            f"💬 {raw_msg}\n"
            f"👤 Owner: `{uid_owner or 'Unknown'}`"
        )
        try:
            http_requests.post(tg_url, json={
                "chat_id": SUPER_ADMIN,
                "text": admin_txt,
                "parse_mode": "Markdown"
            }, timeout=5)
        except: pass

        return "OK", 200
    except Exception as e:
        return str(e), 500

Thread(target=lambda: flask_app.run(host='0.0.0.0', port=8000), daemon=True).start()

# ════════════════════════════════════════════════════════════
#  DATABASE
# ════════════════════════════════════════════════════════════
DB = os.path.join(os.path.dirname(BOT_FILE), 'bot_database.db')
db = sqlite3.connect(DB, check_same_thread=False)
c  = db.cursor()

c.executescript('''
CREATE TABLE IF NOT EXISTS premium_stock(id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT, service TEXT, number TEXT UNIQUE, status INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS active_countries(
    country_name TEXT, short_name TEXT PRIMARY KEY, flag TEXT);
CREATE TABLE IF NOT EXISTS bot_users(user_id INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS bot_links(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS bot_settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS user_lang(user_id INTEGER PRIMARY KEY, lang TEXT DEFAULT "en");
CREATE TABLE IF NOT EXISTS admins(user_id INTEGER PRIMARY KEY, added_by INTEGER, added_at TEXT);
CREATE TABLE IF NOT EXISTS sms_panels(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
    panel_type TEXT, value TEXT, added_at TEXT);
CREATE TABLE IF NOT EXISTS history(user_id INTEGER, date TEXT,
    otp_count INTEGER DEFAULT 0, numbers_taken INTEGER DEFAULT 0,
    PRIMARY KEY(user_id, date));
CREATE TABLE IF NOT EXISTS force_channels(id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE, label TEXT, added_at TEXT);
CREATE TABLE IF NOT EXISTS otp_log(id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT, sender TEXT, received_at TEXT);
CREATE TABLE IF NOT EXISTS user_number_assignments(
    user_id INTEGER, number TEXT, assigned_at TEXT,
    PRIMARY KEY(user_id, number));
''')

c.execute("INSERT OR IGNORE INTO bot_links VALUES ('otp_group','https://t.me/Tareq_SMS_Pro_OTP')")
c.execute("INSERT OR IGNORE INTO bot_links VALUES ('support_group','https://t.me/unlimited_ws_method')")
c.execute("INSERT OR IGNORE INTO bot_settings VALUES ('numbers_per_user','3')")
c.execute("INSERT OR IGNORE INTO bot_settings VALUES ('ai_api_key','')")
if SUPER_ADMIN:
    c.execute("INSERT OR IGNORE INTO admins VALUES (?,?,?)",
              (SUPER_ADMIN, SUPER_ADMIN, str(datetime.date.today())))

_default_channels = [
    ("UnlimitedWSMethod0",  "📢 Channel 1"),
    ("QueenIraMoniBithiBD", "📢 Channel 2"),
    ("QueenIraMoniBithi_BD","💬 Group 1"),
    ("unlimited_ws_method", "💬 Group 2"),
    ("Tareq_SMS_Pro_OTP",   "🔥 OTP Group"),
]
for _u, _l in _default_channels:
    c.execute("INSERT OR IGNORE INTO force_channels(username,label,added_at) VALUES(?,?,?)",
              (_u, _l, str(datetime.date.today())))

c.execute("SELECT id FROM sms_panels WHERE name='ivasms.com' ORDER BY id")
ivasms = c.fetchall()
if not ivasms:
    c.execute("INSERT INTO sms_panels(name,panel_type,value,added_at) VALUES(?,?,?,?)",
              ("ivasms.com","url","https://www.ivasms.com/portal/sms/received",str(datetime.date.today())))
elif len(ivasms) > 1:
    for row in ivasms[1:]: c.execute("DELETE FROM sms_panels WHERE id=?", (row[0],))

db.commit()

c.execute("SELECT id, number FROM premium_stock")
bad = [r[0] for r in c.fetchall()
       if not re.fullmatch(r'\+?\d{6,15}', re.sub(r'[\s\-\(\)\.]','', str(r[1]).strip()))]
if bad:
    c.execute(f"DELETE FROM premium_stock WHERE id IN ({','.join('?'*len(bad))})", bad)
    db.commit()
    print(f"🧹 Cleaned {len(bad)} corrupted numbers")

STATES: dict = {}
SHOWN_IDS: dict = {}

# ════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════
def today(): return str(datetime.date.today())

def is_admin(uid):
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,)); return c.fetchone() is not None

def glang(uid):
    c.execute("SELECT lang FROM user_lang WHERE user_id=?", (uid,))
    r = c.fetchone()
    return r[0] if r else 'en'

def slang(uid, l):
    c.execute("INSERT OR REPLACE INTO user_lang VALUES(?,?)", (uid, l)); db.commit()

def T(uid, en, bn):
    return bn if glang(uid)=='bn' else en

def glink(k, df='https://t.me'):
    c.execute("SELECT value FROM bot_links WHERE key=?", (k,))
    r = c.fetchone(); return r[0] if r else df

def gset(k, df=''):
    c.execute("SELECT value FROM bot_settings WHERE key=?", (k,))
    r = c.fetchone(); return r[0] if r else df

def ctry(short):
    c.execute("SELECT country_name,flag FROM active_countries WHERE short_name=?", (short,))
    r = c.fetchone()
    if r: return r[0], r[1]
    info = COUNTRY_MAP.get(short)
    return (info[0], info[1]) if info else (short.upper(), "🌍")

def quota(): return int(gset('numbers_per_user', '3') or 3)

def valid_phone(s):
    if not isinstance(s, str) or not s.strip(): return False
    cl = re.sub(r'[\s\-\(\)\+\.]', '', s.strip())
    return bool(re.fullmatch(r'\d{6,15}', cl))

def fmt_num(s):
    s = s.strip()
    if s.startswith('+'): return s
    d = re.sub(r'[^\d]', '', s)
    return f"+{d}" if d else s

def inc_hist(uid, otps=0, nums=0):
    td = today()
    c.execute("SELECT otp_count,numbers_taken FROM history WHERE user_id=? AND date=?", (uid, td))
    row = c.fetchone()
    if row: c.execute("UPDATE history SET otp_count=?,numbers_taken=? WHERE user_id=? AND date=?",
                      (row[0]+otps, row[1]+nums, uid, td))
    else:   c.execute("INSERT INTO history VALUES(?,?,?,?)", (uid, td, otps, nums))
    db.commit()

def read_numbers_from_file(path: str, fname: str) -> list:
    nums = []
    try:
        if fname.lower().endswith(('.xlsx','.xls')):
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    for cell in row:
                        if cell is not None:
                            s = str(cell).strip()
                            if s.endswith('.0'): s = s[:-2]
                            nums.append(s)
            wb.close()
        else:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                nums = [l.strip() for l in f if l.strip()]
    except Exception as e:
        print(f"File read error: {e}")
    return nums

# ════════════════════════════════════════════════════════════
#  AI ASSISTANT
# ════════════════════════════════════════════════════════════
SYSTEM_PROMPT = (
    "You are the expert AI assistant for Tareq SMS Pro Telegram bot. "
    "The bot distributes OTP numbers for WhatsApp/Telegram/TikTok/Facebook/Instagram. "
    "Features: force-sub (5 channels), 100+ countries, admin panel, SMS panels, "
    "multi-admin (5), bn/en language, OTP webhook, AI assistant, code editor. "
    "UptimeRobot URL: /alive. Webhook: /webhook/otp."
)
KB = {
    'uptime':    "🔗 UptimeRobot URL:\n`https://[domain]/alive`\nType: HTTP(s), interval: 5 min",
    'upload':    "📁 Upload steps:\nAdmin → 📁 Upload Numbers → Service → Country → send .txt or .xlsx file\n\n✅ .txt: one number per line\n✅ .xlsx: one number per cell",
    'country':   "🌍 Country toggle:\nAdmin → 🌍 Countries → 🌐 World List → tap country to activate (✅)",
    'panel':     "📡 Panel add:\nAdmin → 📡 SMS Panels → ➕ Add Panel → name → URL or API Key",
    'webhook':   "🔗 Webhook: `/webhook/otp`\nParams: sms/message, phone/number, sender",
    'code':      "💻 Bot Code:\nAdmin → 💻 My Bot Code → Download/Edit/Restart/Stop\n✅ Always downloads latest code!",
    'admin':     "👥 Admin:\nAdmin → 👥 Admins → ➕ Add Admin → User ID or @username",
    'restart':   "🔄 Restart:\nAdmin → 💻 My Bot Code → 🔄 Restart Bot",
    'number':    "📱 Get Number:\n/start → 📱 Get Number → Service → Country → tap number to copy it",
    'broadcast': "📣 Broadcast:\nAdmin → 📣 Broadcast → send your message",
}

def ai_reply(question: str, api_key: str = '') -> str:
    q = question.lower()
    if api_key and len(api_key) > 30:
        try:
            r = http_requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": "claude-3-haiku-20240307", "max_tokens": 600,
                      "system": SYSTEM_PROMPT,
                      "messages": [{"role": "user", "content": question}]},
                timeout=20
            )
            if r.ok: return r.json()['content'][0]['text']
        except: pass
    for kw, ans in KB.items():
        if kw in q: return f"🤖 **AI Answer:**\n\n{ans}"
    if any(w in q for w in ['restart','stop','run']): return f"🤖\n\n{KB['restart']}"
    if any(w in q for w in ['number','copy','get']): return f"🤖\n\n{KB['number']}"
    if any(w in q for w in ['xlsx','excel','file']): return f"🤖\n\n{KB['upload']}"
    return ("🤖 Ask me about:\n"
            "• uptime • upload • country • panel • webhook • code • admin • restart • number • broadcast\n\n"
            "💡 Set Anthropic API key for detailed answers.")

# ════════════════════════════════════════════════════════════
#  BOT CLIENT
# ════════════════════════════════════════════════════════════
bot = TelegramClient('tareq_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def set_commands():
    try:
        await bot(SetBotCommandsRequest(
            scope=BotCommandScopeDefault(), lang_code='',
            commands=[
                BotCommand('start',     'Start Bot'),
                BotCommand('myhistory', 'My History'),
                BotCommand('lang',      'Toggle Language / ভাষা পরিবর্তন'),
            ]
        ))
    except Exception as e: print(f"Commands error: {e}")

def get_force_channels():
    c.execute("SELECT username, label FROM force_channels ORDER BY id")
    return c.fetchall()

async def check_sub(uid):
    bad = []
    for ch, lbl in get_force_channels():
        try: await bot(GetParticipantRequest(channel=ch, participant=uid))
        except: bad.append((ch, lbl))
    return bad

# ════════════════════════════════════════════════════════════
#  COMPACT KEYBOARD
# ════════════════════════════════════════════════════════════
_TGAPI = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_compact_kb(chat_id: int, text: str, lang: str = 'en', parse_mode: str = 'Markdown'):
    http_requests.post(f"{_TGAPI}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "📱 নাম্বার নিন",        "callback_data": "btn_get_number"},
                 {"text": "🌍 দেশ দেখুন",           "callback_data": "btn_countries"}],
                [{"text": "📋 আমার নাম্বার",        "callback_data": "btn_active"},
                 {"text": "🔍 নাম্বার খুঁজুন",      "callback_data": "btn_search"}],
                [{"text": "💬 সাপোর্ট",             "callback_data": "btn_support"},
                 {"text": "👥 রেফার করুন",           "callback_data": "btn_refer"}],
                [{"text": "📊 আমার স্ট্যাটাস",      "callback_data": "btn_status"},
                 {"text": "🌐 ভাষা পরিবর্তন",       "callback_data": "btn_lang"}],
            ]
        }
    }, timeout=10)

def adm_kb():
    return [
        [Button.inline("━━━━ 📦 STOCK ━━━━","adm_dummy")],
        [Button.inline("📁 নাম্বার আপলোড","adm_upload"), Button.inline("📊 স্টক রিপোর্ট","adm_stats")],
        [Button.inline("━━━━ 📈 REPORTS ━━━━","adm_dummy")],
        [Button.inline("📈 ডেইলি রিপোর্ট","adm_daily"),  Button.inline("📣 ব্রডকাস্ট","adm_bc")],
        [Button.inline("━━━━ ⚙️ SETTINGS ━━━━","adm_dummy")],
        [Button.inline("🌍 দেশ ম্যানেজ","adm_countries"), Button.inline("🔢 কোটা সেট","adm_quota")],
        [Button.inline("🔗 লিংক সেটিং","adm_links"),     Button.inline("👥 অ্যাডমিন","adm_admins")],
        [Button.inline("━━━━ 🛠 TOOLS ━━━━","adm_dummy")],
        [Button.inline("📡 SMS প্যানেল","adm_panels"),    Button.inline("💻 বট কোড","adm_code")],
        [Button.inline("🤖 AI অ্যাসিস্ট্যান্ট","adm_ai")],
        [Button.inline("👁 ইউজার ভিউ","view_user")],
    ]

# ════════════════════════════════════════════════════════════
#  SHOW NUMBERS  — copy_text buttons (tap = instant copy)
# ════════════════════════════════════════════════════════════
async def show_numbers(event, uid, svc, short, edit=True, reset_shown=False):
    c_name, c_flag = ctry(short)
    srv  = SVC.get(svc, svc.upper())
    lim  = quota()
    lang = glang(uid)

    if reset_shown:
        SHOWN_IDS.pop(uid, None)

    seen = SHOWN_IDS.get(uid, set())

    if seen:
        ph = ','.join('?' * len(seen))
        c.execute(
            f"SELECT id,number FROM premium_stock "
            f"WHERE country=? AND service=? AND status=0 AND id NOT IN ({ph}) LIMIT ?",
            (short, svc, *seen, lim))
    else:
        c.execute(
            "SELECT id,number FROM premium_stock "
            "WHERE country=? AND service=? AND status=0 LIMIT ?",
            (short, svc, lim))
    rows = c.fetchall()

    if not rows and seen:
        SHOWN_IDS.pop(uid, None)
        c.execute(
            "SELECT id,number FROM premium_stock "
            "WHERE country=? AND service=? AND status=0 LIMIT ?",
            (short, svc, lim))
        rows = c.fetchall()

    no_msg  = (f"{c_flag} <b>{c_name.upper()}</b> {srv}\n\n"
               + ("❌ No stock. Select another country."
                  if lang=='en' else "❌ স্টক নেই। অন্য দেশ বেছে নিন।"))
    if not rows:
        kbd = [[{"text":"🌍 Change Country","callback_data":f"svc_{svc}"}],
               [{"text":"◀️ Back to Services","callback_data":"select_svc"}]]
        _send_or_edit(event, uid, edit, no_msg, kbd); return

    SHOWN_IDS[uid] = seen | {r[0] for r in rows}
    inc_hist(uid, nums=len(rows))

    now_ts = str(datetime.datetime.now())
    for _did, num in rows:
        nf2 = fmt_num(num)
        c.execute("INSERT OR IGNORE INTO user_number_assignments VALUES(?,?,?)",
                  (uid, nf2, now_ts))
    db.commit()

    caption = ("📋 <b>নাম্বারে ট্যাপ করলেই কপি হয়ে যাবে!</b>"
               if lang=='bn'
               else "📋 <b>Tap a number — it copies instantly!</b>")
    msg = f"{c_flag} <b>{c_name.upper()}</b> {srv}\n\n{caption}"

    kbd = []
    for _db_id, num in rows:
        nf = fmt_num(num)
        kbd.append([{"text": f"{c_flag} 📋  {nf}", "copy_text": {"text": nf}}])

    kbd += [
        [{"text":"🔄 Change Number","callback_data":f"chg_{svc}_{short}"},
         {"text":"🌍 Change Country","callback_data":f"svc_{svc}"}],
        [{"text":"📢 OTP Group ↗","url": glink("otp_group")}],
    ]
    if is_admin(uid):
        kbd.append([{"text":"🛠 Admin Panel","callback_data":"go_admin"}])

    _send_or_edit(event, uid, edit, msg, kbd)

def _send_or_edit(event, uid: int, edit: bool, text: str, inline_keyboard: list):
    """Send or edit a message using HTTP Bot API with HTML parse mode."""
    payload = {"chat_id": uid, "text": text,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": inline_keyboard}}
    if edit:
        try:
            mid = event.query.msg_id
            http_requests.post(f"{_TGAPI}/editMessageText",
                               json={**payload, "message_id": mid}, timeout=10)
        except Exception:
            http_requests.post(f"{_TGAPI}/sendMessage", json=payload, timeout=10)
    else:
        http_requests.post(f"{_TGAPI}/sendMessage", json=payload, timeout=10)

# ════════════════════════════════════════════════════════════
#  /start
# ════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/start$'))
async def on_start(event):
    if event.is_channel or event.is_group: return
    uid = event.sender_id
    c.execute("INSERT OR IGNORE INTO bot_users VALUES (?)", (uid,)); db.commit()

    if is_admin(uid):
        c.execute("SELECT COUNT(*) FROM premium_stock WHERE status=0"); stock = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM bot_users"); users = c.fetchone()[0]
        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑  **ADMIN CONTROL CENTER**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 Live Stock  ›  {STATUS(stock, 1)}\n"
            f"👥 Total Users  ›  ✅ **{users}**\n\n"
            f"📊 Stock Bar: {PROG(min(stock,100), 100)}\n\n"
            f"⚡ Select an option below 👇\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
        )
        await event.respond(txt, buttons=adm_kb(), parse_mode='md'); return

    bad = await check_sub(uid)
    if bad:
        btns = [[Button.url(lbl, f"https://t.me/{ch}")] for ch, lbl in bad]
        btns.append([Button.inline("✅ আমি জয়েন করেছি — Verify করুন 🔄", "vsub")])
        join_txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔐  **ACCESS REQUIRED**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ নিচের সব channel/group জয়েন করুন\n"
            f"তারপর Verify বাটন চাপুন!\n\n"
            f"📌 জয়েন না করলে বট ব্যবহার করা যাবে না\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
        )
        await event.respond(join_txt, buttons=btns, parse_mode='md'); return

    lang = glang(uid)
    send_compact_kb(uid,
        (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥  *TAREQ SMS PRO*  🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎉 *স্বাগতম! Welcome!*\n\n"
        "📲 Unlimited OTP Method চালু\n"
        "💰 প্রতিদিন ৫০০–১০০০ টাকা আয়ের সুযোগ\n\n"
        "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        "✅ WhatsApp  ✅ Telegram  ✅ TikTok\n"
        "✅ Facebook  ✅ Instagram\n\n"
        "👇 নিচের মেনু থেকে শুরু করুন!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
    ),
        lang=lang)

# ════════════════════════════════════════════════════════════
#  Menu commands
# ════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/myhistory$'))
async def on_history(event):
    if event.is_channel or event.is_group: return
    uid = event.sender_id; lang = glang(uid)
    c.execute("SELECT otp_count,numbers_taken FROM history WHERE user_id=? AND date=?", (uid, today()))
    row = c.fetchone(); o = row[0] if row else 0; n = row[1] if row else 0
    if lang == 'bn':
        txt = f"📝 **আজকের হিস্টোরি**\n\n📱 নাম্বার নিয়েছেন: **{n}** টি"
        if o > 0: txt += f"\n✅ OTP রিসিভ হয়েছে: **{o}** টি"
        else: txt += "\n⏳ এখনো কোনো OTP রিসিভ হয়নি"
    else:
        txt = f"📝 **Today's History**\n\n📱 Numbers taken: **{n}**"
        if o > 0: txt += f"\n✅ OTPs received: **{o}**"
        else: txt += "\n⏳ No OTP received yet today"
    await event.respond(txt, parse_mode='md')

@bot.on(events.NewMessage(pattern=r'^/lang$'))
async def on_lang(event):
    if event.is_channel or event.is_group: return
    uid = event.sender_id
    nl = 'bn' if glang(uid)=='en' else 'en'
    slang(uid, nl)
    send_compact_kb(uid,
        "✅ Language → English\\! Tap *Get Number* to start\\." if nl=='en'
        else "✅ ভাষা বাংলায় পরিবর্তন হয়েছে। *Get Number* চাপুন।",
        lang=nl)

# ════════════════════════════════════════════════════════════
#  /add  (manual)
# ════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/add (.+) (.+) (.+)$'))
async def on_add(event):
    if not is_admin(event.sender_id): return
    short = event.pattern_match.group(1).strip().lower()
    svc   = event.pattern_match.group(2).strip().lower()
    num   = event.pattern_match.group(3).strip()
    if not valid_phone(num): await event.respond("❌ Invalid number."); return
    try:
        c.execute("INSERT INTO premium_stock(country,service,number,status)VALUES(?,?,?,0)",
                  (short, svc, fmt_num(num))); db.commit()
        cn, cf = ctry(short)
        await event.respond(f"✅ Added: {cf} {cn} — {fmt_num(num)}")
    except sqlite3.IntegrityError:
        await event.respond("⚠️ Already exists!")

# ════════════════════════════════════════════════════════════
#  MESSAGE HANDLER
# ════════════════════════════════════════════════════════════
@bot.on(events.NewMessage())
async def on_msg(event):
    if event.is_channel or event.is_group: return
    uid  = event.sender_id
    text = (event.text or '').strip()
    lang = glang(uid)

    if event.file and STATES.get(uid,'').startswith("up_"):
        rest  = STATES.pop(uid)[3:]
        parts = rest.split("_", 1)
        short = parts[0]; svc = parts[1] if len(parts)>1 else "whatsapp"
        fname = event.file.name or 'file.txt'
        ext   = os.path.splitext(fname.lower())[1]

        if ext not in ('.txt','.csv','.xlsx','.xls'):
            await event.respond(
                "❌ Send **.txt** or **.xlsx** file only!",
                buttons=[[Button.inline("🔙","adm_upload")]], parse_mode='md')
            STATES[uid] = f"up_{short}_{svc}"; return

        path   = await event.download_media()
        nums   = read_numbers_from_file(path, fname)
        added  = 0; skipped = 0
        for num in nums:
            if valid_phone(num):
                try:
                    c.execute("INSERT INTO premium_stock(country,service,number,status)VALUES(?,?,?,0)",
                              (short, svc, fmt_num(num))); added += 1
                except sqlite3.IntegrityError: pass
            elif num: skipped += 1
        db.commit()
        try: os.remove(path)
        except: pass

        cn, cf = ctry(short)
        alert = (f"🎉 New Numbers Available!\n\n"
                 f"{cf} **{cn.upper()}** {SVC.get(svc,svc)}\n"
                 f"🆕 New stock: **{added}** numbers!\n\nUse /start to get your numbers!")
        c.execute("SELECT user_id FROM bot_users")
        for (u,) in c.fetchall():
            try: await bot.send_message(u, alert, parse_mode='md')
            except: pass

        await event.respond(
            f"✅ Upload complete!\n{cf} {cn} — {SVC.get(svc,svc)}\n"
            f"➕ Added: **{added}** | ⏭ Skipped: **{skipped}**",
            buttons=adm_kb(), parse_mode='md'); return

    if event.file and STATES.get(uid) == "new_code":
        STATES.pop(uid)
        fname = event.file.name or ''
        if not fname.lower().endswith('.py'):
            await event.respond("❌ Send a .py file!", buttons=[[Button.inline("🔙","adm_code")]]); return
        path = await event.download_media()
        try:
            with open(path,'r',encoding='utf-8') as f: code = f.read()
            try: os.remove(path)
            except: pass
            with open(BOT_FILE,'w',encoding='utf-8') as f: f.write(code)
            await event.respond("✅ Code saved! Restarting...", buttons=[[Button.inline("🔙","adm_code")]])
            time.sleep(1); os.execv(sys.executable, [sys.executable]+sys.argv)
        except Exception as e:
            await event.respond(f"❌ {e}", buttons=[[Button.inline("🔙","adm_code")]]); return

    if not text or uid not in STATES: return
    state = STATES.pop(uid)

    if state == "search":
        c.execute("SELECT number,country,service FROM premium_stock "
                  "WHERE number LIKE ? AND status=0 LIMIT 10", (f"%{text}%",))
        rows = c.fetchall()
        if rows:
            out = f"🔍 Results ({len(rows)}):\n\n"
            for num, ct, sv in rows:
                cn, cf = ctry(ct)
                out += f"{cf} {cn} — {SVC.get(sv,sv)}\n📞 `{fmt_num(num)}`\n\n"
        else:
            out = f"❌ No result for '{text}'."
        await event.respond(out, parse_mode='md'); return

    if state == "bc":
        c.execute("SELECT user_id FROM bot_users"); cnt = 0
        for (u,) in c.fetchall():
            try: await bot.send_message(u, text); cnt += 1
            except: pass
        await event.respond(f"✅ Broadcast → {cnt} users.", buttons=adm_kb()); return

    if state == "otp_link":
        c.execute("INSERT OR REPLACE INTO bot_links VALUES('otp_group',?)", (text,)); db.commit()
        await event.respond("✅ OTP link updated.", buttons=adm_kb()); return

    if state == "sup_link":
        c.execute("INSERT OR REPLACE INTO bot_links VALUES('support_group',?)", (text,)); db.commit()
        await event.respond("✅ Support link updated.", buttons=adm_kb()); return

    if state == "quota":
        if text.isdigit() and 1 <= int(text) <= 10:
            c.execute("INSERT OR REPLACE INTO bot_settings VALUES('numbers_per_user',?)", (text,)); db.commit()
            await event.respond(f"✅ Quota set: {text} numbers/user.", buttons=adm_kb())
        else: await event.respond("❌ Enter a number 1-10.", buttons=adm_kb())
        return

    if state == "add_adm":
        uid_to_add = None
        if text.isdigit():
            uid_to_add = int(text)
        elif text.startswith('@') or re.match(r'^[a-zA-Z]', text):
            try:
                entity = await bot.get_entity(text.lstrip('@'))
                uid_to_add = entity.id
            except Exception as e:
                await event.respond(f"❌ Username not found: {e}", buttons=adm_kb()); return
        else:
            await event.respond("❌ Send User ID or @username.", buttons=adm_kb()); return
        c.execute("SELECT COUNT(*) FROM admins"); cnt = c.fetchone()[0]
        if cnt >= 5:
            await event.respond("❌ Max 5 admins reached.", buttons=adm_kb()); return
        c.execute("INSERT OR IGNORE INTO admins VALUES(?,?,?)", (uid_to_add, uid, today())); db.commit()
        await event.respond(f"✅ Admin added: `{uid_to_add}`", buttons=adm_kb(), parse_mode='md'); return

    if state == "pname":
        STATES[uid] = f"pval_{text}"
        await event.respond(f"📡 **{text}**\n\nSend the URL or API Key:",
                            buttons=[[Button.inline("🔙","adm_panels")]], parse_mode='md'); return

    if state.startswith("pval_"):
        pname = state[5:]; ptype = "url" if text.startswith("http") else "apikey"
        c.execute("SELECT COUNT(*) FROM sms_panels"); cnt = c.fetchone()[0]
        if cnt >= 20:
            await event.respond("❌ Max 20 panels.", buttons=adm_kb())
        else:
            c.execute("INSERT INTO sms_panels(name,panel_type,value,added_at)VALUES(?,?,?,?)",
                      (pname, ptype, text, today())); db.commit()
            await event.respond(f"✅ Panel added: **{pname}** ({ptype.upper()})",
                                buttons=adm_kb(), parse_mode='md')
        return

    if state == "set_ai_key":
        c.execute("INSERT OR REPLACE INTO bot_settings VALUES('ai_api_key',?)", (text,)); db.commit()
        await event.respond("✅ AI API Key saved!", buttons=[[Button.inline("🔙","adm_ai")]]); return

    if state == "ai":
        ans = ai_reply(text, gset('ai_api_key',''))
        await event.respond(ans + "\n\n_Ask another question or /start_",
                            buttons=[[Button.inline("❌ Exit","adm_ai")]], parse_mode='md')
        STATES[uid] = "ai"; return

    if state == "fch_username":
        uname = text.lstrip('@').strip()
        if not re.match(r'^[a-zA-Z0-9_]{3,32}$', uname):
            await event.respond("❌ Invalid username. Only letters, numbers, _ allowed (3-32 chars).",
                                buttons=[[Button.inline("🔙","adm_links")]]); return
        chs = get_force_channels()
        if len(chs) >= 10:
            await event.respond("❌ Max 10 force channels reached!", buttons=[[Button.inline("🔙","adm_links")]]); return
        STATES[uid] = f"fch_label_{uname}"
        await event.respond(
            f"✅ Username: @{uname}\n\nNow send a label (e.g. `📢 Channel 3`):",
            buttons=[[Button.inline("🔙","adm_links")]], parse_mode='md'); return

    if state.startswith("fch_label_"):
        uname = state[10:]
        label = text.strip()[:30]
        try:
            c.execute("INSERT OR IGNORE INTO force_channels(username,label,added_at) VALUES(?,?,?)",
                      (uname, label, today())); db.commit()
            await event.respond(
                f"✅ Force channel added!\n@{uname} — {label}",
                buttons=[[Button.inline("🔗 Links Menu","adm_links")]], parse_mode='md')
        except Exception as e:
            await event.respond(f"❌ Error: {e}", buttons=[[Button.inline("🔙","adm_links")]])
        return

# ════════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ════════════════════════════════════════════════════════════
@bot.on(events.CallbackQuery)
async def on_cb(event):
    data = event.data.decode(); uid = event.sender_id; lang = glang(uid)

    # ── Main Menu Inline Buttons ─────────────────────────────────
    if data == "btn_get_number":
        await event.answer()
        STATES.pop(uid, None)
        await bot.send_message(uid,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📱  **সার্ভিস সিলেক্ট করুন**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔽 নিচে থেকে আপনার পছন্দের সার্ভিস বেছে নিন:",
            buttons=[
                [Button.inline("💬 WhatsApp","svc_whatsapp"), Button.inline("🔹 Telegram","svc_telegram")],
                [Button.inline("🎵 TikTok",  "svc_tiktok"),  Button.inline("🌐 Facebook","svc_facebook")],
                [Button.inline("📸 Instagram","svc_instagram")],
                [Button.inline("🏠 হোমে ফিরুন","view_user")]]); return

    if data == "btn_countries":
        await event.answer()
        c.execute("""SELECT a.country_name, a.short_name, a.flag,
                            COUNT(p.id) as cnt
                     FROM active_countries a
                     LEFT JOIN premium_stock p ON p.country=a.short_name AND p.status=0
                     GROUP BY a.short_name ORDER BY a.country_name""")
        rows = c.fetchall()
        if not rows:
            await bot.send_message(uid,
                "❌ No active countries yet." if lang=='en' else "❌ কোনো দেশ এখনো সক্রিয় নেই।"); return
        txt = ("🌍 **Available Countries:**\n\n" if lang=='en'
               else "🌍 **উপলব্ধ দেশসমূহ:**\n\n")
        for cname, cshort, cflag, cnt in rows:
            txt += f"{cflag} {cname} — **{cnt}** numbers\n"
        await bot.send_message(uid, txt, parse_mode='md'); return

    if data == "btn_active":
        await event.answer()
        c.execute("""SELECT una.number, ps.service, ps.country
                     FROM user_number_assignments una
                     LEFT JOIN premium_stock ps ON REPLACE(REPLACE(ps.number,'+',''),'-','')
                                                 = REPLACE(REPLACE(una.number,'+',''),'-','')
                     WHERE una.user_id=?
                     ORDER BY una.assigned_at DESC LIMIT 10""", (uid,))
        rows = c.fetchall()
        if not rows:
            await bot.send_message(uid,
                "📊 You haven't taken any numbers yet." if lang=='en'
                else "📊 আপনি এখনো কোনো নাম্বার নেননি।"); return
        txt = ("📊 **Your Active Numbers:**\n\n" if lang=='en'
               else "📊 **আপনার নাম্বারসমূহ:**\n\n")
        for num, svc_k, cshort in rows:
            cn, cf = ctry(cshort or ''); srv = SVC.get(svc_k, svc_k or 'Unknown')
            txt += f"{cf} `{num}` — {srv}\n"
        await bot.send_message(uid, txt, parse_mode='md'); return

    if data == "btn_search":
        await event.answer()
        STATES[uid] = "search"
        await bot.send_message(uid,
            "🔍 Type a number or prefix:" if lang=='en' else "🔍 নাম্বার বা প্রিফিক্স টাইপ করুন:"); return

    if data == "btn_support":
        await event.answer()
        sup = glink('support_group', 'https://t.me/unlimited_ws_method')
        txt = (f"💬 **Support**\n\nFor help contact our admin:\n{sup}"
               if lang=='en'
               else f"💬 **সাপোর্ট**\n\nযেকোনো সমস্যায় যোগাযোগ করুন:\n{sup}")
        await bot.send_message(uid, txt, parse_mode='md',
                               buttons=[[Button.url("💬 Support Group ↗", sup)]]); return

    if data == "btn_refer":
        await event.answer()
        me = await bot.get_me()
        ref_link = f"https://t.me/{me.username}?start=ref_{uid}"
        txt = (f"👥 **Refer & Earn**\n\n🔗 Your referral link:\n`{ref_link}`\n\nShare with friends!"
               if lang=='en'
               else f"👥 **রেফার করুন**\n\n🔗 আপনার রেফারেল লিংক:\n`{ref_link}`\n\nবন্ধুদের সাথে শেয়ার করুন!")
        await bot.send_message(uid, txt, parse_mode='md',
                               buttons=[[Button.url("🔗 Share Link ↗", ref_link)]]); return

    if data == "btn_status":
        await event.answer()
        c.execute("SELECT otp_count, numbers_taken FROM history WHERE user_id=? AND date=?",
                  (uid, today()))
        row = c.fetchone(); o = row[0] if row else 0; n = row[1] if row else 0
        c.execute("SELECT COUNT(*) FROM user_number_assignments WHERE user_id=?", (uid,))
        total_nums = c.fetchone()[0]
        lang_label = "বাংলা 🇧🇩" if lang=='bn' else "English 🇬🇧"
        otp_bar  = PROG(o, max(o,10))
        num_bar  = PROG(n, max(n,10))
        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤  **আমার প্রোফাইল**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 আইডি    › `{uid}`\n"
            f"🌐 ভাষা    › {lang_label}\n\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"📊 **আজকের অ্যাক্টিভিটি:**\n\n"
            f"📱 নাম্বার নিয়েছেন › **{n}** টি\n"
            f"   {num_bar}\n\n"
            f"✅ OTP পেয়েছেন    › **{o}** টি\n"
            f"   {otp_bar}\n\n"
        )
        if total_nums > 0:
            txt += f"📦 মোট নাম্বার (সব সময়) › **{total_nums}** টি\n\n"
        txt += (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
        )
        await bot.send_message(uid, txt, parse_mode='md'); return

    if data == "btn_lang":
        await event.answer()
        nl = 'bn' if glang(uid)=='en' else 'en'
        slang(uid, nl)
        send_compact_kb(uid,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌐  **ভাষা পরিবর্তন সফল!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            + ("✅ Language changed to *English* 🇬🇧\n\nTap below to continue 👇"
               if nl=='en' else
               "✅ ভাষা *বাংলা* তে পরিবর্তন হয়েছে 🇧🇩\n\nনিচে থেকে চালিয়ে যান 👇"),
            lang=nl); return

    if data == "vsub":
        bad = await check_sub(uid)
        if bad:
            await event.answer("❌ You haven't joined yet!", alert=True); return
        await event.answer("✅ Verified! Welcome.", alert=False)
        await event.delete()
        send_compact_kb(uid,
            "🔥 *Tareq SMS Pro* ✅\n\n"
            + ("📲 Unlimited Method Active\n💰 Earn 500-1000 BDT daily"
               if lang=='en' else
               "📲 Unlimited Method চালু\n💰 প্রতিদিন ৫০০-১০০০ টাকা"),
            lang=lang); return


    if data.startswith("chg_"):
        parts = data.split("_", 2)
        svc   = parts[1]; short = parts[2]
        await show_numbers(event, uid, svc, short, edit=True); return

    if data == "adm_back":
        STATES.pop(uid, None)
        c.execute("SELECT COUNT(*) FROM premium_stock WHERE status=0"); stock = c.fetchone()[0]
        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑  **ADMIN CONTROL CENTER**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 Live Stock  ›  {STATUS(stock, 1)}\n"
            f"📊 Stock Bar: {PROG(min(stock,100), 100)}\n\n"
            f"⚡ Select an option below 👇\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
        )
        await event.edit(txt, buttons=adm_kb(), parse_mode='md'); return

    if data == "view_user":
        await event.delete()
        send_compact_kb(uid,
            "🔥 *Tareq SMS Pro* ✅\n\n"
            + ("📲 Unlimited Method Active\n💰 Earn 500-1000 BDT daily"
               if lang=='en' else "📲 Unlimited Method চালু\n💰 প্রতিদিন ৫০০-১০০০ টাকা"),
            lang=lang); return

    if data == "go_admin":
        if not is_admin(uid): await event.answer("❌ Access denied.", alert=True); return
        c.execute("SELECT COUNT(*) FROM premium_stock WHERE status=0"); stock = c.fetchone()[0]
        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑  **ADMIN CONTROL CENTER**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 Live Stock  ›  {STATUS(stock, 1)}\n"
            f"📊 Stock Bar: {PROG(min(stock,100), 100)}\n\n"
            f"⚡ Select an option below 👇\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
        )
        await event.edit(txt, buttons=adm_kb(), parse_mode='md'); return

    if data == "select_svc":
        await event.edit(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📱  **সার্ভিস সিলেক্ট করুন**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "নিচে থেকে আপনার পছন্দের সার্ভিস বেছে নিন 👇",
            buttons=[
                [Button.inline("💬 WhatsApp","svc_whatsapp"), Button.inline("🔹 Telegram","svc_telegram")],
                [Button.inline("🎵 TikTok",  "svc_tiktok"),  Button.inline("🌐 Facebook","svc_facebook")],
                [Button.inline("📸 Instagram","svc_instagram")],
                [Button.inline("🏠 হোমে ফিরুন","view_user")]]); return

    if data.startswith("svc_"):
        svc = data[4:]
        c.execute("SELECT DISTINCT p.country FROM premium_stock p "
                  "JOIN active_countries a ON a.short_name=p.country "
                  "WHERE p.service=? AND p.status=0", (svc,))
        ws = {r[0] for r in c.fetchall()}
        if not ws:
            await event.edit(f"❌ No stock for {SVC.get(svc,svc)}.",
                             buttons=[[Button.inline("◀️ Back","select_svc")]]); return
        btns = []; row = []
        for short in sorted(ws):
            cn, cf = ctry(short)
            nm = cn[:8] if len(cn)>8 else cn
            row.append(Button.inline(f"{cf} {nm} [{short.upper()}]", f"ctry_{svc}_{short}"))
            if len(row)==2: btns.append(row); row=[]
        if row: btns.append(row)
        btns.append([Button.inline("◀️ Back to Services","select_svc")])
        await event.edit(f"🌍 Select Country for {SVC.get(svc,svc)}:", buttons=btns); return

    if data.startswith("ctry_"):
        _, svc, short = data.split("_", 2)
        SHOWN_IDS.pop(uid, None)
        await show_numbers(event, uid, svc, short, edit=True); return

    if data == "adm_dummy":
        await event.answer("", alert=False); return

    if not is_admin(uid):
        await event.answer("❌ Admin only.", alert=True); return

    if data == "adm_stats":
        c.execute("SELECT country,service,COUNT(*) FROM premium_stock WHERE status=0 GROUP BY country,service")
        rows = c.fetchall()
        c.execute("SELECT COUNT(*) FROM bot_users"); users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM premium_stock WHERE status=0"); total = c.fetchone()[0]
        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊  **STOCK REPORT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 মোট ইউজার  ›  ✅ **{users}**\n"
            f"📦 মোট স্টক   ›  {STATUS(total, 1)}\n\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"🗂 **দেশ ও সার্ভিস অনুযায়ী:**\n\n"
        )
        for ct, sv, cnt_val in rows:
            cn, cf = ctry(ct)
            bar = PROG(min(cnt_val,20), 20, 8)
            txt += f"{cf} {cn} › {SVC.get(sv,sv)}\n{bar} **{cnt_val}** নাম্বার\n\n"
        if not rows: txt += "❌ কোনো স্টক নেই।"
        txt += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
        await event.edit(txt, buttons=[[Button.inline("🔙 ফিরে যান","adm_back")]], parse_mode='md'); return

    if data == "adm_daily":
        td = today()
        c.execute("SELECT COUNT(*) FROM otp_log WHERE received_at LIKE ?", (f"{td}%",))
        total_otp = c.fetchone()[0]
        c.execute("SELECT SUM(numbers_taken) FROM history WHERE date=?", (td,))
        total_nums = c.fetchone()[0] or 0
        c.execute("SELECT SUM(otp_count) FROM history WHERE date=?", (td,))
        total_otp_users = c.fetchone()[0] or 0
        c.execute("""SELECT user_id, numbers_taken, otp_count FROM history
                     WHERE date=? ORDER BY numbers_taken DESC LIMIT 10""", (td,))
        user_rows = c.fetchall()
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈  **DAILY REPORT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 তারিখ › **{td}**\n\n"
            f"📥 মোট OTP এসেছে   › {STATUS(total_otp, 1)}\n"
            f"📱 মোট নাম্বার নেওয়া › {STATUS(total_nums, 1)}\n"
            f"✅ ইউজারদের OTP    › {STATUS(total_otp_users, 1)}\n\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"🏆 **আজকের টপ ইউজার:**\n\n"
        )
        if user_rows:
            for i, (u_id, u_nums, u_otp) in enumerate(user_rows, 1):
                medal = medals[i-1] if i <= len(medals) else f"{i}."
                txt += f"{medal} `{u_id}`\n   📱 {u_nums} নাম্বার | ✅ {u_otp} OTP\n\n"
        else:
            txt += "⚠️ আজ কোনো অ্যাক্টিভিটি নেই।"
        txt += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💎 *Tareq SMS Pro* | 🔥 Premium OTP Bot"
        await event.edit(txt, buttons=[[Button.inline("🔙 ফিরে যান","adm_back")]], parse_mode='md'); return

    if data == "adm_quota":
        STATES[uid] = "quota"
        await event.edit(f"🔢 Numbers per user (current: {quota()})\n\nSend 1-10:",
                         buttons=[[Button.inline("🔙","adm_back")]]); return

    if data == "adm_bc":
        STATES[uid] = "bc"
        c.execute("SELECT COUNT(*) FROM bot_users"); n = c.fetchone()[0]
        await event.edit(f"📣 Broadcast to {n} users\n\nSend your message:",
                         buttons=[[Button.inline("🔙","adm_back")]]); return

    if data == "adm_links":
        chs = get_force_channels()
        txt = (f"🔗 **Links & Force Channels**\n\n"
               f"📢 OTP Link: {glink('otp_group')}\n"
               f"💬 Support: {glink('support_group')}\n\n"
               f"🔒 **Force Channels** ({len(chs)}/10):\n")
        for u, l in chs:
            txt += f"• {l} — @{u}\n"
        btns = [
            [Button.inline("✏️ OTP Link","edit_otp"), Button.inline("✏️ Support Link","edit_sup")],
            [Button.inline("➕ Add Force Channel","add_fch")],
        ]
        for ch_u, ch_l in chs:
            btns.append([Button.inline(f"❌ Remove {ch_l} (@{ch_u})", f"rmfch_{ch_u}")])
        btns.append([Button.inline("🔙","adm_back")])
        await event.edit(txt, buttons=btns, parse_mode='md'); return

    if data == "edit_otp":
        STATES[uid] = "otp_link"
        await event.edit("✏️ Send new OTP group link:", buttons=[[Button.inline("🔙","adm_links")]]); return

    if data == "edit_sup":
        STATES[uid] = "sup_link"
        await event.edit("✏️ Send new support link:", buttons=[[Button.inline("🔙","adm_links")]]); return

    if data == "add_fch":
        chs = get_force_channels()
        if len(chs) >= 10:
            await event.answer("❌ Max 10 channels reached!", alert=True); return
        STATES[uid] = "fch_username"
        await event.edit(
            "➕ **Add Force Channel/Group**\n\nSend the @username (without @):\nExample: `MyChannel`",
            buttons=[[Button.inline("🔙","adm_links")]], parse_mode='md'); return

    if data.startswith("rmfch_"):
        ch_u = data[6:]
        c.execute("DELETE FROM force_channels WHERE username=?", (ch_u,)); db.commit()
        await event.answer(f"✅ @{ch_u} removed!", alert=False)
        chs = get_force_channels()
        txt = (f"🔗 **Links & Force Channels**\n\n"
               f"📢 OTP Link: {glink('otp_group')}\n"
               f"💬 Support: {glink('support_group')}\n\n"
               f"🔒 **Force Channels** ({len(chs)}/10):\n")
        for u, l in chs:
            txt += f"• {l} — @{u}\n"
        btns = [
            [Button.inline("✏️ OTP Link","edit_otp"), Button.inline("✏️ Support Link","edit_sup")],
            [Button.inline("➕ Add Force Channel","add_fch")],
        ]
        for ch_u2, ch_l2 in chs:
            btns.append([Button.inline(f"❌ Remove {ch_l2} (@{ch_u2})", f"rmfch_{ch_u2}")])
        btns.append([Button.inline("🔙","adm_back")])
        await event.edit(txt, buttons=btns, parse_mode='md'); return

    if data == "adm_admins":
        c.execute("SELECT user_id FROM admins"); adms = c.fetchall()
        txt = f"👥 **Admins** ({len(adms)}/5)\n\n"; btns = []
        for (aid,) in adms:
            sup = aid == SUPER_ADMIN
            txt += f"{'👑' if sup else '🔹'} `{aid}`{'  (Super)' if sup else ''}\n"
            if not sup: btns.append([Button.inline(f"❌ Remove {aid}", f"rmadm_{aid}")])
        if len(adms) < 5:
            btns.append([Button.inline("➕ Add Admin (ID or @username)","addadm")])
        btns.append([Button.inline("🔙","adm_back")])
        await event.edit(txt, buttons=btns, parse_mode='md'); return

    if data == "addadm":
        STATES[uid] = "add_adm"
        await event.edit("➕ Send User ID or @username:",
                         buttons=[[Button.inline("🔙","adm_admins")]]); return

    if data.startswith("rmadm_"):
        if uid != SUPER_ADMIN: await event.answer("❌ Super Admin only.", alert=True); return
        rid = int(data[6:])
        c.execute("DELETE FROM admins WHERE user_id=?", (rid,)); db.commit()
        await event.answer(f"✅ Removed {rid}", alert=False)
        c.execute("SELECT user_id FROM admins"); adms = c.fetchall()
        txt = f"👥 **Admins** ({len(adms)}/5)\n\n"; btns = []
        for (aid,) in adms:
            sup = aid == SUPER_ADMIN
            txt += f"{'👑' if sup else '🔹'} `{aid}`{'  (Super)' if sup else ''}\n"
            if not sup: btns.append([Button.inline(f"❌ Remove {aid}", f"rmadm_{aid}")])
        if len(adms) < 5: btns.append([Button.inline("➕ Add Admin","addadm")])
        btns.append([Button.inline("🔙","adm_back")])
        await event.edit(txt, buttons=btns, parse_mode='md'); return

    if data == "adm_panels":
        c.execute("SELECT id,name,panel_type,value FROM sms_panels ORDER BY id"); pnls = c.fetchall()
        txt = f"📡 **SMS Panels** ({len(pnls)}/20)\n\n"; btns = []
        for pid, nm, pt, v in pnls:
            d = v[:38]+"…" if len(v)>38 else v
            txt += f"🔹 **{nm}** `{pt.upper()}`\n`{d}`\n\n"
            btns.append([Button.inline(f"🔗 {nm}", f"opn_{pid}"),
                         Button.inline("❌", f"rmpnl_{pid}")])
        if len(pnls) < 20: btns.append([Button.inline("➕ Add Panel","add_panel")])
        btns.append([Button.inline("🔙","adm_back")])
        await event.edit(txt or "📡 No panels.", buttons=btns, parse_mode='md'); return

    if data == "add_panel":
        STATES[uid] = "pname"
        await event.edit("📡 Send panel name (e.g. hero-sms.com):",
                         buttons=[[Button.inline("🔙","adm_panels")]]); return

    if data.startswith("opn_"):
        pid = int(data[4:])
        c.execute("SELECT name,panel_type,value FROM sms_panels WHERE id=?", (pid,))
        r = c.fetchone()
        if not r: await event.answer("Not found.", alert=True); return
        nm, pt, v = r
        if pt == "url":
            await event.edit(f"📡 **{nm}**\n\n🔗 {v}",
                             buttons=[[Button.url(f"🔗 Open {nm}", v)],
                                      [Button.inline("🔙","adm_panels")]], parse_mode='md')
        else:
            await event.edit(f"📡 **{nm}**\n\n🔑 API Key:\n`{v}`\n\n(Tap to copy)",
                             buttons=[[Button.inline("🔙","adm_panels")]], parse_mode='md')
        return

    if data.startswith("rmpnl_"):
        pid = int(data[6:])
        c.execute("SELECT name FROM sms_panels WHERE id=?", (pid,)); r = c.fetchone()
        if r:
            c.execute("DELETE FROM sms_panels WHERE id=?", (pid,)); db.commit()
            await event.answer(f"✅ {r[0]} removed!", alert=False)
        c.execute("SELECT id,name,panel_type,value FROM sms_panels ORDER BY id"); pnls = c.fetchall()
        txt = f"📡 **SMS Panels** ({len(pnls)}/20)\n\n"; btns = []
        for pid2, nm2, pt2, v2 in pnls:
            d = v2[:38]+"…" if len(v2)>38 else v2
            txt += f"🔹 **{nm2}** `{pt2.upper()}`\n`{d}`\n\n"
            btns.append([Button.inline(f"🔗 {nm2}", f"opn_{pid2}"),
                         Button.inline("❌", f"rmpnl_{pid2}")])
        if len(pnls) < 20: btns.append([Button.inline("➕ Add Panel","add_panel")])
        btns.append([Button.inline("🔙","adm_back")])
        await event.edit(txt or "📡 No panels.", buttons=btns, parse_mode='md'); return

    if data == "adm_countries":
        await event.edit("🌍 **Country Management**", buttons=[
            [Button.inline("🌐 World List (Toggle)","world_0")],
            [Button.inline("📋 Active List","list_c")],
            [Button.inline("🔙","adm_back")]], parse_mode='md'); return

    if data.startswith("world_"):
        pg = int(data[6:]); per = 12; st = pg*per; chunk = COUNTRIES[st:st+per]
        c.execute("SELECT short_name FROM active_countries"); active = {r[0] for r in c.fetchall()}
        btns = []; row = []
        for cn, sh, fl in chunk:
            on = sh in active
            nm = cn[:9] if len(cn)>9 else cn
            row.append(Button.inline(f"{'✅' if on else ''}{fl} {nm} [{sh.upper()}]", f"tgl_{sh}"))
            if len(row)==2: btns.append(row); row=[]
        if row: btns.append(row)
        nav = []
        if pg > 0:          nav.append(Button.inline("◀️ Prev", f"world_{pg-1}"))
        if st+per<len(COUNTRIES): nav.append(Button.inline("Next ▶️", f"world_{pg+1}"))
        if nav: btns.append(nav)
        btns.append([Button.inline("🔙","adm_countries")])
        tp = (len(COUNTRIES)+per-1)//per
        await event.edit(f"🌍 Countries — Page {pg+1}/{tp}  (✅ = Active, tap to toggle)",
                         buttons=btns); return

    if data.startswith("tgl_"):
        sh = data[4:]
        c.execute("SELECT 1 FROM active_countries WHERE short_name=?", (sh,))
        if c.fetchone():
            c.execute("DELETE FROM active_countries WHERE short_name=?", (sh,))
            c.execute("DELETE FROM premium_stock WHERE country=?", (sh,))
            db.commit(); await event.answer(f"✅ {sh.upper()} deactivated", alert=False)
        else:
            info = COUNTRY_MAP.get(sh)
            if info:
                c.execute("INSERT OR IGNORE INTO active_countries VALUES(?,?,?)",
                          (info[0], sh, info[1])); db.commit()
                await event.answer(f"✅ {info[1]} {info[0]} activated!", alert=False)
        idx = next((i for i,(_, s, _) in enumerate(COUNTRIES) if s==sh), 0)
        pg = idx//12; per = 12; st = pg*per; chunk = COUNTRIES[st:st+per]
        c.execute("SELECT short_name FROM active_countries"); active = {r[0] for r in c.fetchall()}
        btns = []; row = []
        for cn, s2, fl in chunk:
            on = s2 in active
            nm = cn[:9] if len(cn)>9 else cn
            row.append(Button.inline(f"{'✅' if on else ''}{fl} {nm} [{s2.upper()}]", f"tgl_{s2}"))
            if len(row)==2: btns.append(row); row=[]
        if row: btns.append(row)
        nav = []
        if pg > 0:            nav.append(Button.inline("◀️ Prev", f"world_{pg-1}"))
        if st+per<len(COUNTRIES): nav.append(Button.inline("Next ▶️", f"world_{pg+1}"))
        if nav: btns.append(nav)
        btns.append([Button.inline("🔙","adm_countries")])
        tp = (len(COUNTRIES)+per-1)//per
        await event.edit(f"🌍 Countries — Page {pg+1}/{tp}  (✅ = Active):", buttons=btns); return

    if data == "list_c":
        c.execute("SELECT country_name,short_name,flag FROM active_countries ORDER BY country_name")
        rows = c.fetchall(); txt = "📋 **Active Countries:**\n\n"; btns = []
        for cn, sh, fl in rows:
            c.execute("SELECT COUNT(*) FROM premium_stock WHERE country=? AND status=0", (sh,))
            cnt_val = c.fetchone()[0]
            txt += f"{fl} {cn} [{sh.upper()}] — **{cnt_val}**\n"
            btns.append([Button.inline(f"❌ {fl} {cn} [{sh.upper()}]", f"delc_{sh}")])
        if not rows: txt += "❌ None active."
        btns.append([Button.inline("🔙","adm_countries")])
        await event.edit(txt, buttons=btns, parse_mode='md'); return

    if data.startswith("delc_"):
        sh = data[5:]
        c.execute("DELETE FROM active_countries WHERE short_name=?", (sh,))
        c.execute("DELETE FROM premium_stock WHERE country=?", (sh,)); db.commit()
        await event.answer(f"✅ {sh.upper()} removed!", alert=False)
        c.execute("SELECT country_name,short_name,flag FROM active_countries ORDER BY country_name")
        rows = c.fetchall(); txt = "📋 **Active Countries:**\n\n"; btns = []
        for cn, sh2, fl in rows:
            c.execute("SELECT COUNT(*) FROM premium_stock WHERE country=? AND status=0", (sh2,))
            cnt_val = c.fetchone()[0]
            txt += f"{fl} {cn} [{sh2.upper()}] — **{cnt_val}**\n"
            btns.append([Button.inline(f"❌ {fl} {cn} [{sh2.upper()}]", f"delc_{sh2}")])
        if not rows: txt += "❌ None active."
        btns.append([Button.inline("🔙","adm_countries")])
        await event.edit(txt, buttons=btns, parse_mode='md'); return

    if data == "adm_upload":
        await event.edit("📁 Select service:", buttons=[
            [Button.inline("💬 WhatsApp","up_whatsapp"), Button.inline("🔹 Telegram","up_telegram")],
            [Button.inline("🎵 TikTok",  "up_tiktok"),  Button.inline("🌐 Facebook","up_facebook")],
            [Button.inline("📸 Instagram","up_instagram")],
            [Button.inline("🔙","adm_back")]]); return

    if data.startswith("up_") and not data.startswith("upc_"):
        svc = data[3:]
        c.execute("SELECT country_name,short_name,flag FROM active_countries ORDER BY country_name")
        rows = c.fetchall()
        if not rows:
            await event.answer("❌ No active countries! Go to Countries first.", alert=True); return
        btns = []; row = []
        for cn, sh, fl in rows:
            nm = cn[:8] if len(cn)>8 else cn
            row.append(Button.inline(f"{fl} {nm} [{sh.upper()}]", f"upc_{svc}_{sh}"))
            if len(row)==2: btns.append(row); row=[]
        if row: btns.append(row)
        btns.append([Button.inline("🔙","adm_upload")])
        await event.edit(f"📁 {SVC.get(svc,svc)} — Select Country:", buttons=btns); return

    if data.startswith("upc_"):
        rest = data[4:]; pts = rest.split("_",1); svc = pts[0]; sh = pts[1] if len(pts)>1 else "eg"
        STATES[uid] = f"up_{sh}_{svc}"
        cn, cf = ctry(sh)
        await event.edit(
            f"📥 **Upload Numbers**\n{cf} **{cn}** [{sh.upper()}] — {SVC.get(svc,svc)}\n\n"
            f"✅ Send **.txt** file (one number per line)\n"
            f"✅ Send **.xlsx** file (one number per cell in Excel)",
            buttons=[[Button.inline("🔙","adm_upload")]], parse_mode='md'); return

    if data == "adm_code":
        try:
            sz    = os.path.getsize(BOT_FILE)
            with open(BOT_FILE,'r',encoding='utf-8') as f: lines = f.read().count('\n')
            mt    = datetime.datetime.fromtimestamp(os.path.getmtime(BOT_FILE)).strftime("%Y-%m-%d %H:%M")
        except: sz=0; lines=0; mt="N/A"
        await event.edit(
            f"💻 **My Bot Code**\n\n"
            f"📄 main.py | 📏 {lines} lines | 💾 {sz//1024} KB\n"
            f"🕐 Modified: {mt}\n\n"
            f"✅ **Auto-updated** — always downloads latest code!\n\n"
            f"Features: Force Sub • 5 Services • 100+ Countries\n"
            f"SMS Panels (20) • Multi-Admin (5) • TXT+XLSX Upload\n"
            f"@username Admin • OTP Webhook • AI Assistant",
            buttons=[
                [Button.inline("📄 Download Code","code_dl")],
                [Button.inline("✏️ Upload New Code (.py)","code_edit")],
                [Button.inline("🔄 Restart Bot","code_restart")],
                [Button.inline("⏹ Stop Bot","code_stop")],
                [Button.inline("🔙","adm_back")],
            ], parse_mode='md'); return

    if data == "code_dl":
        await event.answer("📄 Sending file...", alert=False)
        try:
            await bot.send_file(uid, BOT_FILE,
                caption=f"💻 **Tareq SMS Pro Bot Code**\n📅 {today()}\n📏 Complete — always up to date!",
                parse_mode='md')
            await event.edit("✅ Code file sent! Check above ☝️",
                             buttons=[[Button.inline("🔙","adm_code")]])
        except Exception as e:
            await event.edit(f"❌ Error: {e}", buttons=[[Button.inline("🔙","adm_code")]])
        return

    if data == "code_edit":
        STATES[uid] = "new_code"
        await event.edit(
            "✏️ **Edit Bot Code**\n\nSend updated .py file.\nBot will auto-restart after save.\n\n"
            "⚠️ Caution: wrong code may stop the bot!",
            buttons=[[Button.inline("❌ Cancel","adm_code")]], parse_mode='md'); return

    if data == "code_restart":
        await event.edit("🔄 Restarting bot...", buttons=[])
        time.sleep(1); os.execv(sys.executable, [sys.executable]+sys.argv)

    if data == "code_stop":
        await event.edit("⏹ Bot stopping. Workflow will restart automatically.", buttons=[])
        time.sleep(2); sys.exit(0)

    if data == "adm_ai":
        STATES.pop(uid, None)
        key = gset('ai_api_key','')
        ks = "✅ Anthropic API set" if key else "⚠️ No API key — built-in KB active"
        await event.edit(
            f"🤖 **AI Bot Assistant**\n\nStatus: {ks}\n\n"
            f"Ask about: uptime • upload • country\npanel • webhook • code • admin • restart",
            buttons=[
                [Button.inline("💬 Ask a Question","ai_chat")],
                [Button.inline("🔑 Set Anthropic API Key","ai_setkey")],
                [Button.inline("🔙","adm_back")],
            ], parse_mode='md'); return

    if data == "ai_setkey":
        STATES[uid] = "set_ai_key"
        await event.edit("🔑 Send Anthropic API Key (https://console.anthropic.com):",
                         buttons=[[Button.inline("🔙","adm_ai")]]); return

    if data == "ai_chat":
        STATES[uid] = "ai"
        await event.edit("💬 **AI Chat Active**\n\nType your question...\n_/start to exit_",
                         buttons=[[Button.inline("❌ Exit","adm_ai")]]); return

# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════
import asyncio

async def main():
    await set_commands()
    print("✅ Tareq SMS Pro Bot is online!")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    bot.loop.run_until_complete(main())
