import os, sys, re, sqlite3, datetime, time
import requests as http_requests
from threading import Thread, Lock

from flask import Flask, request as flask_req
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommand, BotCommandScopeDefault
import openpyxl

# ════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════
API_ID      = 30334076        # ← এখানে তোমার API_ID বসাও (my.telegram.org থেকে)
API_HASH    = '59792fbc49ed08135f985c6c312c9b52'  # ← এখানে তোমার API_HASH বসাও
BOT_TOKEN   = '8667327104:AAG2uG6K4rZcodX0LZ73p2Iv7hdA-iwN_qs'
SUPER_ADMIN = 8890678382
OTP_GROUP   = -1004355081956
BOT_FILE    = os.path.abspath(__file__)

# ── 2oo9 OTP API — admin panel থেকে পরিবর্তন করা যাবে না ──
OTP_API_BASE = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
OTP_API_KEY  = "YOUR_API_KEY"  # ← এখানে তোমার mauthapi key বসাও

# ── Owner name (admin panel থেকেও পরিবর্তন করা যাবে) ──
DEFAULT_OWNER_NAME = "OTP Zone"

# ── শুধু এই একটা channel join required ──
OTP_CHANNEL_USERNAME = "otp_zon"
OTP_CHANNEL_LABEL    = "🔥 OTP Zone"
OTP_CHANNEL_URL      = "https://t.me/otp_zon"

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
    base = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 *OTP Zone* | Premium OTP Bot"
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

_DEBUG_OTP_LOG: list = []  # [(phone, sender, raw_msg, otp_code), ...]

@flask_app.route('/debug/otp')
def debug_otp():
    key = flask_req.args.get('key', '')
    if key != OTP_API_KEY:
        return "Unauthorized", 403
    lines = []
    for i, (ph, snd, msg, code) in enumerate(_DEBUG_OTP_LOG[-10:], 1):
        lines.append(f"#{i} phone={ph} sender={snd}\n  msg={repr(msg)}\n  otp={repr(code)}\n")
    return "<pre>" + "\n".join(lines) + "</pre>" if lines else "No OTP received yet"

@flask_app.route('/')
def home(): return "✅ OTP Zone Bot is running!"

@flask_app.route('/alive')
def alive(): return "OK", 200

# ── সাময়িক maintenance route — শুধু force_channels table clean করার জন্য।
#    OTP logic/poller/webhook-কে এটা একদমই টাচ করে না। কাজ শেষ হলে এই
#    route + এর নিচের লাইনটা bot.py থেকে মুছে ফেলাই নিরাপদ। ──
@flask_app.route('/admin/fix-force-channel')
def fix_force_channel():
    key = flask_req.args.get('key')
    if key != OTP_API_KEY:
        return "Unauthorized", 403
    with _db_lock:
        c.execute("SELECT username FROM force_channels")
        before = [r[0] for r in c.fetchall()]
        c.execute("DELETE FROM force_channels WHERE username != ?", (OTP_CHANNEL_USERNAME,))
        db.commit()
        c.execute("SELECT username FROM force_channels")
        after = [r[0] for r in c.fetchall()]
    return f"Before: {before} → After: {after}", 200

_TG_SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def process_incoming_otp(raw_msg: str, phone: str, sender: str = 'Unknown', source: str = 'webhook'):
    """
    Central OTP pipeline — used by the /webhook/otp endpoint AND by the
    SMS-panel auto-fetcher.
      • OTP সরাসরি OTP channel-এ পাঠায়
      • Number match হলে user-কে শুধু Number + OTP পাঠায়
      • Super admin-কে alert করে
    Returns True if a matching owner was found, else False.
    """
    global bot, db, c
    if not raw_msg or not phone:
        return False

    now  = str(datetime.datetime.now())
    norm = re.sub(r'[^\d]', '', phone)

    with _db_lock:
        # ── Log the OTP ──
        c.execute("INSERT INTO otp_log(phone,sender,received_at,message,matched) VALUES(?,?,?,?,0)",
                  (phone, sender, now, raw_msg))

        # ── Country & service info ──
        c.execute(
            "SELECT country, service FROM premium_stock "
            "WHERE REPLACE(REPLACE(number,'+',''),'-','')=?", (norm,))
        stock_row = c.fetchone()
        country_short = stock_row[0] if stock_row else ''
        service_key   = stock_row[1] if stock_row else ''

    # ── Country: phone number এর prefix দিয়ে detect করো ──
    country_name = 'Unknown'
    country_flag = '🌍'
    if country_short:
        info = COUNTRY_MAP.get(country_short)
        if info:
            country_name, country_flag = info[0], info[1]

    if country_name == 'Unknown':
        # phone number prefix দিয়ে country match করো
        PHONE_PREFIX_MAP = {
            '1': ('USA', 'us', '🇺🇸'), '7': ('Russia', 'ru', '🇷🇺'),
            '20': ('Egypt', 'eg', '🇪🇬'), '27': ('South Africa', 'za', '🇿🇦'),
            '30': ('Greece', 'gr', '🇬🇷'), '31': ('Netherlands', 'nl', '🇳🇱'),
            '32': ('Belgium', 'be', '🇧🇪'), '33': ('France', 'fr', '🇫🇷'),
            '34': ('Spain', 'es', '🇪🇸'), '36': ('Hungary', 'hu', '🇭🇺'),
            '39': ('Italy', 'it', '🇮🇹'), '40': ('Romania', 'ro', '🇷🇴'),
            '41': ('Switzerland', 'ch', '🇨🇭'), '43': ('Austria', 'at', '🇦🇹'),
            '44': ('UK', 'uk', '🇬🇧'), '45': ('Denmark', 'dk', '🇩🇰'),
            '46': ('Sweden', 'se', '🇸🇪'), '47': ('Norway', 'no', '🇳🇴'),
            '48': ('Poland', 'pl', '🇵🇱'), '49': ('Germany', 'de', '🇩🇪'),
            '51': ('Peru', 'pe', '🇵🇪'), '52': ('Mexico', 'mx', '🇲🇽'),
            '54': ('Argentina', 'ar', '🇦🇷'), '55': ('Brazil', 'br', '🇧🇷'),
            '56': ('Chile', 'cl', '🇨🇱'), '57': ('Colombia', 'co', '🇨🇴'),
            '58': ('Venezuela', 've', '🇻🇪'), '60': ('Malaysia', 'my', '🇲🇾'),
            '61': ('Australia', 'au', '🇦🇺'), '62': ('Indonesia', 'id', '🇮🇩'),
            '63': ('Philippines', 'ph', '🇵🇭'), '64': ('New Zealand', 'nz', '🇳🇿'),
            '65': ('Singapore', 'sg', '🇸🇬'), '66': ('Thailand', 'th', '🇹🇭'),
            '81': ('Japan', 'jp', '🇯🇵'), '82': ('South Korea', 'kr', '🇰🇷'),
            '84': ('Vietnam', 'vn', '🇻🇳'), '86': ('China', 'cn', '🇨🇳'),
            '90': ('Turkey', 'tr', '🇹🇷'), '91': ('India', 'in', '🇮🇳'),
            '92': ('Pakistan', 'pk', '🇵🇰'), '93': ('Afghanistan', 'af', '🇦🇫'),
            '94': ('Sri Lanka', 'lk', '🇱🇰'), '95': ('Myanmar', 'mm', '🇲🇲'),
            '98': ('Iran', 'ir', '🇮🇷'),
            '212': ('Morocco', 'ma', '🇲🇦'), '213': ('Algeria', 'dz', '🇩🇿'),
            '216': ('Tunisia', 'tn', '🇹🇳'), '218': ('Libya', 'ly', '🇱🇾'),
            '220': ('Gambia', 'gm', '🇬🇲'), '221': ('Senegal', 'sn', '🇸🇳'),
            '223': ('Mali', 'ml', '🇲🇱'), '224': ('Guinea', 'gn', '🇬🇳'),
            '225': ('Ivory Coast', 'ci', '🇨🇮'), '227': ('Niger', 'ne', '🇳🇪'),
            '228': ('Togo', 'tg', '🇹🇬'), '229': ('Benin', 'bj', '🇧🇯'),
            '230': ('Mauritius', 'mu', '🇲🇺'), '231': ('Liberia', 'lr', '🇱🇷'),
            '232': ('Sierra Leone', 'sl', '🇸🇱'), '233': ('Ghana', 'gh', '🇬🇭'),
            '234': ('Nigeria', 'ng', '🇳🇬'), '235': ('Chad', 'td', '🇹🇩'),
            '236': ('Congo', 'cg', '🇨🇬'), '237': ('Cameroon', 'cm', '🇨🇲'),
            '238': ('Cape Verde', 'cv', '🇨🇻'), '239': ('Sao Tome', 'st', '🇸🇹'),
            '240': ('Equatorial Guinea', 'gq', '🇬🇶'), '241': ('Gabon', 'ga', '🇬🇦'),
            '242': ('Congo', 'cg', '🇨🇬'), '243': ('DR Congo', 'cd', '🇨🇩'),
            '244': ('Angola', 'ao', '🇦🇴'), '245': ('Guinea-Bissau', 'gw', '🇬🇼'),
            '246': ('British Indian Ocean', 'io', '🌍'), '247': ('Ascension', 'ac', '🌍'),
            '248': ('Seychelles', 'sc', '🇸🇨'), '249': ('Sudan', 'sd', '🇸🇩'),
            '250': ('Rwanda', 'rw', '🇷🇼'), '251': ('Ethiopia', 'et', '🇪🇹'),
            '252': ('Somalia', 'so', '🇸🇴'), '253': ('Djibouti', 'dj', '🇩🇯'),
            '254': ('Kenya', 'ke', '🇰🇪'), '255': ('Tanzania', 'tz', '🇹🇿'),
            '256': ('Uganda', 'ug', '🇺🇬'), '257': ('Burundi', 'bi', '🇧🇮'),
            '258': ('Mozambique', 'mz', '🇲🇿'), '260': ('Zambia', 'zm', '🇿🇲'),
            '261': ('Madagascar', 'mg', '🇲🇬'), '263': ('Zimbabwe', 'zw', '🇿🇼'),
            '264': ('Namibia', 'na', '🇳🇦'), '265': ('Malawi', 'mw', '🇲🇼'),
            '266': ('Lesotho', 'ls', '🇱🇸'), '267': ('Botswana', 'bw', '🇧🇼'),
            '268': ('Swaziland', 'sz', '🇸🇿'), '269': ('Comoros', 'km', '🇰🇲'),
            '290': ('Saint Helena', 'sh', '🌍'), '291': ('Eritrea', 'er', '🇪🇷'),
            '297': ('Aruba', 'aw', '🇦🇼'), '298': ('Faroe Islands', 'fo', '🇫🇴'),
            '299': ('Greenland', 'gl', '🇬🇱'),
            '350': ('Gibraltar', 'gi', '🇬🇮'), '351': ('Portugal', 'pt', '🇵🇹'),
            '352': ('Luxembourg', 'lu', '🇱🇺'), '353': ('Ireland', 'ie', '🇮🇪'),
            '354': ('Iceland', 'is', '🇮🇸'), '355': ('Albania', 'al', '🇦🇱'),
            '356': ('Malta', 'mt', '🇲🇹'), '357': ('Cyprus', 'cy', '🇨🇾'),
            '358': ('Finland', 'fi', '🇫🇮'), '359': ('Bulgaria', 'bg', '🇧🇬'),
            '370': ('Lithuania', 'lt', '🇱🇹'), '371': ('Latvia', 'lv', '🇱🇻'),
            '372': ('Estonia', 'ee', '🇪🇪'), '373': ('Moldova', 'md', '🇲🇩'),
            '374': ('Armenia', 'am', '🇦🇲'), '375': ('Belarus', 'by', '🇧🇾'),
            '376': ('Andorra', 'ad', '🇦🇩'), '377': ('Monaco', 'mc', '🇲🇨'),
            '380': ('Ukraine', 'ua', '🇺🇦'), '381': ('Serbia', 'rs', '🇷🇸'),
            '382': ('Montenegro', 'me', '🇲🇪'), '385': ('Croatia', 'hr', '🇭🇷'),
            '386': ('Slovenia', 'si', '🇸🇮'), '387': ('Bosnia', 'ba', '🇧🇦'),
            '389': ('North Macedonia', 'mk', '🇲🇰'),
            '420': ('Czech Republic', 'cz', '🇨🇿'), '421': ('Slovakia', 'sk', '🇸🇰'),
            '423': ('Liechtenstein', 'li', '🇱🇮'),
            '500': ('Falkland Islands', 'fk', '🌍'), '501': ('Belize', 'bz', '🇧🇿'),
            '502': ('Guatemala', 'gt', '🇬🇹'), '503': ('El Salvador', 'sv', '🇸🇻'),
            '504': ('Honduras', 'hn', '🇭🇳'), '505': ('Nicaragua', 'ni', '🇳🇮'),
            '506': ('Costa Rica', 'cr', '🇨🇷'), '507': ('Panama', 'pa', '🇵🇦'),
            '509': ('Haiti', 'ht', '🇭🇹'),
            '591': ('Bolivia', 'bo', '🇧🇴'), '592': ('Guyana', 'gy', '🇬🇾'),
            '593': ('Ecuador', 'ec', '🇪🇨'), '595': ('Paraguay', 'py', '🇵🇾'),
            '597': ('Suriname', 'sr', '🇸🇷'), '598': ('Uruguay', 'uy', '🇺🇾'),
            '599': ('Netherlands Antilles', 'an', '🌍'),
            '670': ('East Timor', 'tl', '🇹🇱'), '672': ('Norfolk Island', 'nf', '🌍'),
            '673': ('Brunei', 'bn', '🇧🇳'), '674': ('Nauru', 'nr', '🇳🇷'),
            '675': ('Papua New Guinea', 'pg', '🇵🇬'), '676': ('Tonga', 'to', '🇹🇴'),
            '677': ('Solomon Islands', 'sb', '🇸🇧'), '678': ('Vanuatu', 'vu', '🇻🇺'),
            '679': ('Fiji', 'fj', '🇫🇯'), '680': ('Palau', 'pw', '🇵🇼'),
            '682': ('Cook Islands', 'ck', '🇨🇰'), '685': ('Samoa', 'ws', '🇼🇸'),
            '686': ('Kiribati', 'ki', '🇰🇮'), '687': ('New Caledonia', 'nc', '🇳🇨'),
            '688': ('Tuvalu', 'tv', '🇹🇻'), '689': ('French Polynesia', 'pf', '🇵🇫'),
            '690': ('Tokelau', 'tk', '🌍'), '691': ('Micronesia', 'fm', '🇫🇲'),
            '692': ('Marshall Islands', 'mh', '🇲🇭'),
            '850': ('North Korea', 'kp', '🇰🇵'), '852': ('Hong Kong', 'hk', '🇭🇰'),
            '853': ('Macau', 'mo', '🇲🇴'), '855': ('Cambodia', 'kh', '🇰🇭'),
            '856': ('Laos', 'la', '🇱🇦'),
            '880': ('Bangladesh', 'bd', '🇧🇩'), '886': ('Taiwan', 'tw', '🇹🇼'),
            '960': ('Maldives', 'mv', '🇲🇻'), '961': ('Lebanon', 'lb', '🇱🇧'),
            '962': ('Jordan', 'jo', '🇯🇴'), '963': ('Syria', 'sy', '🇸🇾'),
            '964': ('Iraq', 'iq', '🇮🇶'), '965': ('Kuwait', 'kw', '🇰🇼'),
            '966': ('Saudi Arabia', 'sa', '🇸🇦'), '967': ('Yemen', 'ye', '🇾🇪'),
            '968': ('Oman', 'om', '🇴🇲'), '970': ('Palestine', 'ps', '🇵🇸'),
            '971': ('UAE', 'ae', '🇦🇪'), '972': ('Israel', 'il', '🇮🇱'),
            '973': ('Bahrain', 'bh', '🇧🇭'), '974': ('Qatar', 'qa', '🇶🇦'),
            '975': ('Bhutan', 'bt', '🇧🇹'), '976': ('Mongolia', 'mn', '🇲🇳'),
            '977': ('Nepal', 'np', '🇳🇵'),
            '992': ('Tajikistan', 'tj', '🇹🇯'), '993': ('Turkmenistan', 'tm', '🇹🇲'),
            '994': ('Azerbaijan', 'az', '🇦🇿'), '995': ('Georgia', 'ge', '🇬🇪'),
            '996': ('Kyrgyzstan', 'kg', '🇰🇬'), '998': ('Uzbekistan', 'uz', '🇺🇿'),
        }
        # longest prefix match করো
        for plen in (3, 2, 1):
            prefix = norm[:plen]
            if prefix in PHONE_PREFIX_MAP:
                cdata = PHONE_PREFIX_MAP[prefix]
                country_name, country_short, country_flag = cdata
                break

    # ── Service: sender name + SMS text থেকে detect করো (20 popular apps) ──
    APP_DETECT = [
        (('whatsapp',),                                           'whatsapp',   'WhatsApp'),
        (('telegram',),                                           'telegram',   'Telegram'),
        (('tiktok', 'tik tok', 'tik-tok'),                        'tiktok',     'TikTok'),
        (('facebook', ' fb ', 'meta'),                            'facebook',   'Facebook'),
        (('instagram', 'insta'),                                  'instagram',  'Instagram'),
        (('twitter', 'x.com', 'twtr'),                            'twitter',    'Twitter/X'),
        (('snapchat', 'snap'),                                    'snapchat',   'Snapchat'),
        (('google', 'gmail', 'youtube'),                          'google',     'Google'),
        (('amazon', 'amzn', 'aws'),                               'amazon',     'Amazon'),
        (('apple', 'icloud', 'itunes'),                           'apple',      'Apple'),
        (('microsoft', 'outlook', 'hotmail', 'msft'),             'microsoft',  'Microsoft'),
        (('paypal',),                                             'paypal',     'PayPal'),
        (('uber', 'ubereats'),                                    'uber',       'Uber'),
        (('netflix',),                                            'netflix',    'Netflix'),
        (('linkedin',),                                           'linkedin',   'LinkedIn'),
        (('discord',),                                            'discord',    'Discord'),
        (('binance', 'coinbase', 'bybit', 'kucoin', 'crypto'),    'crypto',     'Crypto'),
        (('airbnb',),                                             'airbnb',     'Airbnb'),
        (('spotify',),                                            'spotify',    'Spotify'),
        (('shopee', 'lazada', 'tokopedia', 'shein', 'aliexpress'),'shop',       'Shopping'),
    ]

    detected_brand = None
    if not service_key:
        check_text = (sender + ' ' + raw_msg).lower()
        for keywords, skey, brand in APP_DETECT:
            if any(kw in check_text for kw in keywords):
                service_key    = skey
                detected_brand = brand
                break

    svc_name = detected_brand or SVC.get(service_key, 'Other')
    masked   = mask_number(phone)

    # ── SMS থেকে OTP code extract করো ──
    def extract_otp(text: str) -> str:
        """SMS text থেকে OTP code extract করে।
        Handles: 567-853 (WhatsApp dash format), 123456 (plain), code: 1234
        """
        if not text:
            return ''

        # Priority 1: WhatsApp style — NNN-NNN (3-3 digit with dash) → join করে 6-digit বানাও
        # e.g. "567-853", "205-239", "496-439"
        wa = re.search(r'(?<!\d)(\d{3})-(\d{3})(?!\d)', text)
        if wa:
            return wa.group(1) + wa.group(2)

        # Priority 2: keyword এর পরে plain number
        # e.g. "code is 157262", "Your verification code is 157262"
        kw = re.search(
            r'(?:code|otp|pin|password|passcode|verification|verif|token|kode)\s*'
            r'(?:is|:|-|=)?\s*(\d{4,8})(?!\d)',
            text, re.IGNORECASE)
        if kw:
            return kw.group(1)

        # Priority 3: standalone 4-8 digit number
        all_nums = re.findall(r'(?<!\d)(\d{4,8})(?!\d)', text)
        if all_nums:
            for length in (6, 5, 4, 7, 8):
                for n in all_nums:
                    if len(n) == length:
                        return n

        return ''

    otp_code = extract_otp(raw_msg)
    print(f"[OTP DEBUG] raw_msg={repr(raw_msg)} | otp_code={repr(otp_code)} | sender={repr(sender)}")
    _DEBUG_OTP_LOG.append((phone, sender, raw_msg, otp_code))
    if len(_DEBUG_OTP_LOG) > 50:
        _DEBUG_OTP_LOG.pop(0)

    # ── Service brand name (OTP-channel display only — no circle emoji) ──
    # NOTE: Telegram's Bot API cannot embed a real brand-logo image inside a
    # text bubble — only emoji/text are possible. As the closest equivalent
    # to a "real logo" without emoji, we show the clean brand name in bold.
    SVC_BRAND_NAME = {
        'whatsapp':  'WhatsApp',
        'telegram':  'Telegram',
        'tiktok':    'TikTok',
        'facebook':  'Facebook',
        'instagram': 'Instagram',
    }
    svc_brand = detected_brand or SVC_BRAND_NAME.get(service_key) or 'Other'

    # ── Country short code (2-letter uppercase) ──
    country_code = country_short.upper() if country_short else '??'

    # ── Language detect from sender / default EN ──
    lang_code = 'EN'

    # ── Star rating from phone number (last 2 digits → 0-200 scale visual) ──
    star_count = int(norm[-3:]) % 200 + 50 if len(norm) >= 3 else 113

    # ── Info card text — compact Telegram-bubble style ──
    info_line = (
        f"{country_flag} <b>{country_code}</b> » <b>{svc_brand}</b> » {masked} "
        f"⭐{star_count} • {lang_code}"
    )

    # ── OTP button text ──
    otp_display = otp_code if otp_code else "------"

    # ── OTP dash format for display (e.g. 567853 → 567-853) ──
    if otp_code and len(otp_code) == 6:
        otp_display_fmt = otp_code[:3] + '-' + otp_code[3:]
    else:
        otp_display_fmt = otp_display

    # ── Bot username for button URLs ──
    _bot_uname = bot_username() or ''
    _btn_url   = f"https://t.me/{_bot_uname}"
    _sprt_url  = f"https://t.me/{_bot_uname}"

    # ── OTP Channel message — SMS Matrix style ──
    group_txt = (
        f"🎉 <b>NEW OTP RECEIVED</b> 🎉\n\n"
        f"🌐 <b>Country:</b> {country_name} {country_flag}\n"
        f"📱 <b>Number:</b> <code>{masked}</code>\n"
        f"💬 <b>Service:</b> {svc_brand}\n"
        f"🔐 <b>OTP:</b> <code>{otp_display_fmt}</code>\n"
        f"🔤 <b>Language:</b> English"
    )

    ch_inline_keyboard = [
        [{"text": f"🛡️ {otp_display_fmt}", "copy_text": {"text": otp_code if otp_code else otp_display_fmt}}],
        [
            {"text": "🤖 Nmbr Bot ↗", "url": _btn_url},
            {"text": "📢 Sprt Grup ↗", "url": _sprt_url},
        ]
    ]

    try:
        ch_resp = http_requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": OTP_GROUP,
                "text": group_txt,
                "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": ch_inline_keyboard}
            }, timeout=8
        )
        print(f"[OTP CHANNEL] ✅ sent — {ch_resp.status_code} {ch_resp.text[:100]}")
        try:
            import time as _t
            msg_id = ch_resp.json().get("result", {}).get("message_id")
            if msg_id:
                _OTP_MSG_IDS.append((msg_id, _t.time()))
        except: pass
    except Exception as ch_err:
        print(f"[OTP CHANNEL] ❌ error: {ch_err}")

    # ── User number match হলে শুধু Number + OTP পাঠাও (details ছাড়া) ──
    with _db_lock:
        c.execute(
            "SELECT user_id FROM user_number_assignments "
            "WHERE REPLACE(REPLACE(number,'+',''),'-','')=?", (norm,))
        owner_row = c.fetchone()
        uid_owner = owner_row[0] if owner_row else None

        if uid_owner:
            c.execute("UPDATE otp_log SET matched=1 WHERE phone=? AND received_at=?", (phone, now))
            td = str(datetime.date.today())
            c.execute("SELECT otp_count FROM history WHERE user_id=? AND date=?", (uid_owner, td))
            h = c.fetchone()
            if h: c.execute("UPDATE history SET otp_count=otp_count+1 WHERE user_id=? AND date=?",
                            (uid_owner, td))
            else: c.execute("INSERT INTO history VALUES(?,?,1,0)", (uid_owner, td))
        db.commit()

    if uid_owner:
        # ── User-এর bot-এ শুধু Number + OTP — clean, minimal ──
        priv_txt = (
            f"📱 `{phone}`\n"
            f"🔐 `{raw_msg}`"
        )
        try:
            http_requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": uid_owner, "text": priv_txt, "parse_mode": "Markdown"},
                timeout=8
            )
            print(f"[OTP DM] ✅ sent to owner {uid_owner}")
        except Exception as dm_err:
            print(f"[OTP DM] ❌ error: {dm_err}")

    # ── Super admin alert ──
    admin_txt = (
        f"📥 *Admin OTP Alert* ({source})\n"
        f"📱 `{phone}` → {country_flag} {country_name} | {svc_name}\n"
        f"💬 Raw: `{raw_msg}`\n"
        f"🔐 OTP extracted: `{otp_code if otp_code else 'NOT FOUND'}`\n"
        f"👤 Owner: `{uid_owner or 'Unknown'}`"
    )
    try:
        http_requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": SUPER_ADMIN, "text": admin_txt, "parse_mode": "Markdown"},
            timeout=8
        )
    except Exception as adm_err:
        print(f"[OTP ADMIN] ❌ error: {adm_err}")

    return uid_owner is not None

_BOT_USERNAME_CACHE = {"v": None}
def bot_username():
    return _BOT_USERNAME_CACHE["v"]

@flask_app.route('/webhook/otp', methods=['GET','POST'])
def otp_hook():
    try:
        d = (flask_req.get_json(silent=True) or flask_req.form
             if flask_req.method=='POST' else flask_req.args)
        raw_msg = (d.get('sms') or d.get('message') or d.get('text') or '').strip()
        phone   = (d.get('phone') or d.get('number') or d.get('sim') or '').strip()
        sender  = (d.get('sender') or d.get('app') or d.get('from') or 'Unknown').strip()
        if not raw_msg: return "no msg", 400
        process_incoming_otp(raw_msg, phone, sender, source='webhook')
        return "OK", 200
    except Exception as e:
        return str(e), 500

Thread(target=lambda: flask_app.run(host='0.0.0.0', port=8000), daemon=True).start()

# ════════════════════════════════════════════════════════════
#  OTP API AUTO-FETCHER — hardcoded API key ব্যবহার করে প্রতি ১৫ সেকেন্ডে
#  OTP channel থেকে নতুন বার্তা টেনে নাম্বার ম্যাচ করলে owner-কে পাঠায়।
# ════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════
#  2oo9 OTP API — getnum / liveaccess / console / success-otp
# ════════════════════════════════════════════════════════════
def _api_headers():
    return {"mauthapi": OTP_API_KEY, "Content-Type": "application/json"}

def api_get_number(rid: str):
    """POST /getnum — নতুন নাম্বার allocate করে।
    Returns dict {full_number, no_plus_number, country, operator} অথবা None (out of stock/error)।
    """
    try:
        r = http_requests.post(f"{OTP_API_BASE}/getnum", headers=_api_headers(),
                                json={"rid": str(rid)}, timeout=15)
        try:
            payload = r.json()
        except Exception as je:
            print(f"[2oo9 API] getnum JSON parse error: {je}")
            return None
        meta = (payload or {}).get("meta", {}) if isinstance(payload, dict) else {}
        if meta.get("code") == 2946:
            print(f"[2oo9 API] getnum — out of stock for rid={rid}")
            return None
        if meta.get("code") != 200:
            print(f"[2oo9 API] getnum failed — meta: {meta}")
            return None
        d = (payload.get("data") or {})
        full_number = str(d.get("full_number", "")).strip()
        if not full_number:
            print("[2oo9 API] getnum returned empty number")
            return None
        return {
            "full_number":    full_number,
            "no_plus_number": str(d.get("no_plus_number", "")).strip(),
            "country":        str(d.get("country", "")).strip(),
            "operator":       str(d.get("operator", "")).strip(),
        }
    except http_requests.exceptions.Timeout:
        print("[2oo9 API] getnum timeout")
        return None
    except Exception as e:
        print(f"[2oo9 API] getnum error: {e}")
        return None

def api_live_services():
    """GET /liveaccess — data.services (active services + ranges) রিটার্ন করে।"""
    try:
        r = http_requests.get(f"{OTP_API_BASE}/liveaccess", headers=_api_headers(), timeout=10)
        payload = r.json()
        meta = (payload or {}).get("meta", {}) if isinstance(payload, dict) else {}
        if meta.get("code") != 200:
            print(f"[2oo9 API] liveaccess failed — meta: {meta}")
            return []
        return (payload.get("data") or {}).get("services", []) or []
    except Exception as e:
        print(f"[2oo9 API] liveaccess error: {e}")
        return []

def api_console_feed():
    """GET /console — data.hits (লাইভ console feed) রিটার্ন করে।"""
    try:
        r = http_requests.get(f"{OTP_API_BASE}/console", headers=_api_headers(), timeout=10)
        payload = r.json()
        meta = (payload or {}).get("meta", {}) if isinstance(payload, dict) else {}
        if meta.get("code") != 200:
            print(f"[2oo9 API] console failed — meta: {meta}")
            return []
        return (payload.get("data") or {}).get("hits", []) or []
    except Exception as e:
        print(f"[2oo9 API] console error: {e}")
        return []


def api_allocate_live(country_short: str, service: str):
    """
    Dynamically allocate a number using:
      1. Pre-configured RID from api_rid_map (all matching rows, not just first).
      2. Fallback: discover active ranges via GET /liveaccess and try every matching RID.
    Normalises all comparisons (lowercase, strip whitespace) to avoid
    Telegram/telegram, WhatsApp/whatsapp, UK/uk mismatches.
    Returns {full_number, no_plus_number, country, operator} or None if all exhausted.
    """
    norm_svc = service.strip().lower()
    norm_cty = country_short.strip().lower()
    print(f"[2oo9 API] Requested service: {norm_svc} | country: {norm_cty}")

    # ── Step 1: try every pre-configured RID ──────────────────────────────────
    with _db_lock:
        c.execute(
            "SELECT rid FROM api_rid_map "
            "WHERE LOWER(TRIM(short_name))=? AND LOWER(TRIM(service))=?",
            (norm_cty, norm_svc))
        configured_rids = [r[0] for r in c.fetchall() if r[0]]

    for rid in configured_rids:
        print(f"[2oo9 API] Selected range (configured): rid={rid}")
        result = api_get_number(rid)
        if result:
            print(f"[2oo9 API] Number allocated: {result.get('full_number')} via rid={rid}")
            return result
        print(f"[2oo9 API] Out of stock: rid={rid} (configured)")

    # ── Step 2: discover via /liveaccess ────────────────────────────────────
    print(f"[2oo9 API] No configured RID succeeded — querying /liveaccess "
          f"for service={norm_svc} country={norm_cty}")
    services = api_live_services()
    if not services:
        print("[2oo9 API] /liveaccess returned no services — giving up")
        return None

    # Collect candidate RIDs: exact country+service match first
    candidate_rids = []
    fallback_rids  = []
    for entry in services:
        if not isinstance(entry, dict):
            continue
        e_svc = str(entry.get("service", "") or "").strip().lower()
        e_cty = str(entry.get("country", "") or "").strip().lower()
        # also check alternative field names
        e_cty_alt = str(entry.get("country_code", "") or entry.get("short", "") or "").strip().lower()
        rid = str(entry.get("rid", "") or "").strip()
        if not rid:
            continue
        if e_svc == norm_svc:
            if e_cty == norm_cty or e_cty_alt == norm_cty:
                candidate_rids.append(rid)
            else:
                fallback_rids.append(rid)  # right service, any country

    # If no exact country match, widen to any country for this service
    if not candidate_rids:
        print(f"[2oo9 API] No exact country match — widening to any country for {norm_svc}")
        candidate_rids = fallback_rids

    # De-duplicate while preserving order (skip already-tried configured ones)
    seen_rids = set(configured_rids)
    unique_candidates = []
    for rid in candidate_rids:
        if rid not in seen_rids:
            seen_rids.add(rid)
            unique_candidates.append(rid)

    print(f"[2oo9 API] Candidate RIDs from /liveaccess: {unique_candidates}")
    for rid in unique_candidates:
        print(f"[2oo9 API] Selected range (live): rid={rid}")
        result = api_get_number(rid)
        if result:
            print(f"[2oo9 API] Number allocated: {result.get('full_number')} via rid={rid}")
            # Cache successful RID so next call is faster
            try:
                with _db_lock:
                    c.execute(
                        "INSERT OR REPLACE INTO api_rid_map(short_name,service,rid) VALUES(?,?,?)",
                        (norm_cty, norm_svc, rid))
                    db.commit()
            except Exception:
                pass
            return result
        print(f"[2oo9 API] Out of stock: rid={rid} (live)")

    print(f"[2oo9 API] All RIDs exhausted for service={norm_svc} country={norm_cty}")
    return None


_SEEN_OTP_IDS: set = set()  # runtime cache — loaded from DB on start, persisted on new entries

# ── OTP Channel Auto-Delete — sent message ID গুলো track করো ──
_OTP_MSG_IDS: list = []  # [(message_id, sent_time), ...]

def _auto_delete_otp_messages():
    """প্রতি ১ মিনিটে check করে — ১০ মিনিট পুরনো OTP message delete করে।"""
    import time as _t
    while True:
        _t.sleep(60)
        try:
            now = _t.time()
            to_delete = [mid for mid, ts in _OTP_MSG_IDS if now - ts >= 600]
            for mid in to_delete:
                try:
                    # Telegram channel থেকে delete
                    http_requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
                        json={"chat_id": OTP_GROUP, "message_id": mid},
                        timeout=5
                    )
                except: pass
            _OTP_MSG_IDS[:] = [(mid, ts) for mid, ts in _OTP_MSG_IDS if now - ts < 600]
            # Database থেকে 10 মিনিটের বেশি পুরনো OTP log delete
            cutoff = str(datetime.datetime.now() - datetime.timedelta(minutes=10))
            with _db_lock:
                c.execute("DELETE FROM otp_log WHERE received_at < ?", (cutoff,))
                db.commit()
        except Exception as e:
            print(f"[AUTO DELETE] error: {e}")

Thread(target=_auto_delete_otp_messages, daemon=True).start()

def poll_otp_api():
    """প্রতি কয়েক সেকেন্ডে GET /success-otp poll করে data.otps থেকে নতুন OTP
    সরাসরি channel-এ পাঠায়। otp_id দিয়ে duplicate ঠেকায়।"""
    global bot
    import time as _time
    while 'bot' not in globals() or bot is None:
        _time.sleep(1)
    print(f"[2oo9 API] OTP Poller started — {OTP_API_BASE}/success-otp")
    while True:
        try:
            r = http_requests.get(f"{OTP_API_BASE}/success-otp", headers=_api_headers(), timeout=10)
            try:
                payload = r.json()
            except Exception as je:
                print(f"[2oo9 API] success-otp JSON parse error: {je} | raw: {r.text[:200]}")
                payload = None

            if payload is None:
                print("[2oo9 API] success-otp empty/invalid response")
            else:
                meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
                if meta.get("code") != 200:
                    # out-of-stock / invalid / non-200 — log করে চালিয়ে যাও, crash করো না
                    print(f"[2oo9 API] success-otp non-200 — meta: {meta}")
                else:
                    otps = (payload.get("data") or {}).get("otps") or []
                    if not isinstance(otps, list):
                        otps = []
                    for item in otps:
                        if not isinstance(item, dict):
                            continue
                        otp_id  = str(item.get("otp_id", "")).strip()
                        number  = str(item.get("number", "")).strip()
                        message = str(item.get("message", "")).strip()
                        if not otp_id or not number or not message:
                            continue

                        with _db_lock:
                            already_seen = otp_id in _SEEN_OTP_IDS
                            if not already_seen:
                                _SEEN_OTP_IDS.add(otp_id)
                                # Persist so duplicates are blocked after restart
                                try:
                                    now_ts = str(datetime.datetime.now())
                                    c.execute(
                                        "INSERT OR IGNORE INTO seen_otp_ids(otp_id,seen_at) VALUES(?,?)",
                                        (otp_id, now_ts))
                                    db.commit()
                                except Exception:
                                    pass
                                # Prune cache if too large
                                if len(_SEEN_OTP_IDS) > 5000:
                                    _SEEN_OTP_IDS.clear()
                                    try:
                                        c.execute(
                                            "DELETE FROM seen_otp_ids WHERE otp_id NOT IN "
                                            "(SELECT otp_id FROM seen_otp_ids ORDER BY rowid DESC LIMIT 3000)")
                                        db.commit()
                                    except Exception:
                                        pass
                        if already_seen:
                            continue  # already sent once — duplicate ঠেকানো হলো

                        try:
                            print(f"[2oo9 API] OTP received: otp_id={otp_id} number={number} msg={message[:80]}")
                            process_incoming_otp(message, number, '2oo9 API', source='api')
                        except Exception as ex:
                            print(f"[2oo9 API] forward error: {ex}")
        except http_requests.exceptions.Timeout:
            print("[2oo9 API] success-otp timeout — will retry")
        except Exception as ex:
            print(f"[2oo9 API] fetch error: {ex}")
        import random as _rand
        time.sleep(_rand.uniform(2, 5))

# poll_otp_api thread — bot init এর পরে start হবে

# ════════════════════════════════════════════════════════════
#  DATABASE
# ════════════════════════════════════════════════════════════
DB = os.path.join(os.path.dirname(BOT_FILE), 'bot_database.db')
db = sqlite3.connect(DB, check_same_thread=False)
db.execute("PRAGMA journal_mode=WAL")   # WAL mode — concurrent read/write hang কমায়
db.execute("PRAGMA busy_timeout=5000")  # 5 সেকেন্ড wait করবে, তারপর error
c  = db.cursor()
_db_lock = Lock()  # SQLite threading lock

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
    phone TEXT, sender TEXT, received_at TEXT,
    message TEXT DEFAULT '', matched INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS user_number_assignments(
    user_id INTEGER, number TEXT, assigned_at TEXT,
    PRIMARY KEY(user_id, number));
CREATE TABLE IF NOT EXISTS api_rid_map(
    short_name TEXT, service TEXT, rid TEXT,
    PRIMARY KEY(short_name, service));
CREATE TABLE IF NOT EXISTS seen_otp_ids(otp_id TEXT PRIMARY KEY, seen_at TEXT);
''')

# force_channels table-এ custom_message column migrate করো
try:
    c.execute("ALTER TABLE force_channels ADD COLUMN custom_message TEXT DEFAULT ''")
    db.commit()
except Exception:
    pass  # column already exists

# Migrate existing otp_log table if columns are missing
for col, defval in [('message', "''"), ('matched', '0')]:
    try:
        c.execute(f"ALTER TABLE otp_log ADD COLUMN {col} TEXT DEFAULT {defval}")
    except Exception:
        pass  # column already exists

c.execute("INSERT OR IGNORE INTO bot_links VALUES ('otp_group','https://t.me/otp_zon')")
c.execute("INSERT OR IGNORE INTO bot_settings VALUES ('numbers_per_user','3')")
c.execute("INSERT OR IGNORE INTO bot_settings VALUES ('ai_api_key','')")
if SUPER_ADMIN:
    c.execute("INSERT OR IGNORE INTO admins VALUES (?,?,?)",
              (SUPER_ADMIN, SUPER_ADMIN, str(datetime.date.today())))

# OTP Zone channel শুরুতে শুধু একবার seed করা হয় — admin যা add/remove করবে তা restart-এ মুছে যাবে না
c.execute("SELECT COUNT(*) FROM force_channels")
if c.fetchone()[0] == 0:
    c.execute("INSERT OR IGNORE INTO force_channels(username,label,added_at) VALUES(?,?,?)",
              (OTP_CHANNEL_USERNAME, OTP_CHANNEL_LABEL, str(datetime.date.today())))

# ⚠️ আগে এখানে 'ivasms.com' নামের একটা panel প্রতি restart-এ অটো re-insert হতো —
# admin ডিলিট করলেও ফিরে আসতো (remove option কাজ করছে না বলে মনে হতো)।
# এছাড়া তার value ছিল একটা ওয়েবপেজ লিংক, JSON API না — তাই auto-fetch কখনো কাজই করতো না।
# এখন কিছুই auto-seed হয় না — admin যা যোগ করবে শুধু তাই থাকবে।

db.commit()

# Load seen OTP IDs from DB into memory cache (survive restarts)
try:
    c.execute("SELECT otp_id FROM seen_otp_ids ORDER BY rowid DESC LIMIT 5000")
    _SEEN_OTP_IDS.update(r[0] for r in c.fetchall())
    print(f"[2oo9 API] Loaded {len(_SEEN_OTP_IDS)} seen OTP IDs from DB")
except Exception as _e:
    print(f"[2oo9 API] Could not load seen_otp_ids: {_e}")

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
    "You are the expert AI assistant for OTP Zone Telegram bot. "
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
bot = TelegramClient('tareq_bot', API_ID, API_HASH)
Thread(target=poll_otp_api, daemon=True).start()

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

def send_nav_kb(chat_id: int, text: str, parse_mode: str = 'Markdown'):
    """নিচে permanent reply keyboard পাঠায় — ঠিক screenshot-এর মতো"""
    http_requests.post(f"{_TGAPI}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": {
            "keyboard": [
                [{"text": "📱 Get Number"},   {"text": "🌍 Available Country"}],
                [{"text": "📋 Active Number"},{"text": "🔍 Search Number"}],
                [{"text": "👥 Refer"},        {"text": "📊 My Status"}],
            ],
            "resize_keyboard": True,
            "persistent": True
        }
    }, timeout=10)

# backward compat alias
def send_compact_kb(chat_id: int, text: str, lang: str = 'en', parse_mode: str = 'Markdown'):
    send_nav_kb(chat_id, text, parse_mode)

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
        [Button.inline("📡 OTP স্ট্যাটাস","adm_panels"),   Button.inline("💻 বট কোড","adm_code")],
        [Button.inline("🤖 AI অ্যাসিস্ট্যান্ট","adm_ai"), Button.inline("📋 OTP লগ","adm_otp_log")],
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

    # ── Stock খালি হলে — live allocation (api_allocate_live auto-discovers RID) ──
    if not rows:
        print(f"[2oo9 API] premium_stock empty for country={short} service={svc} — starting live allocation")
        allocated = 0
        for _ in range(lim):
            info = api_allocate_live(short, svc)
            if not info:
                break  # all RIDs exhausted — চালিয়ে যাও, crash করো না
            try:
                with _db_lock:
                    c.execute(
                        "INSERT OR IGNORE INTO premium_stock(country,service,number,status) VALUES(?,?,?,0)",
                        (short, svc, info["full_number"]))
                    db.commit()
                allocated += 1
            except Exception as ie:
                print(f"[2oo9 API] store number error: {ie}")
        if allocated:
            print(f"[2oo9 API] Allocated {allocated} number(s) into premium_stock for {short}/{svc}")
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
    with _db_lock:
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
        [{"text":f"🔥 {OTP_CHANNEL_LABEL}", "url": OTP_CHANNEL_URL}],
        [{"text":"◀️ Back","callback_data":"select_svc"}],
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
            f"🔥 *OTP Zone* | Premium OTP Bot"
        )
        await event.respond(txt, buttons=adm_kb(), parse_mode='md'); return

    bad = await check_sub(uid)
    if bad:
        # ── Custom message + channel buttons build করো ──
        btns = []
        for ch_u, ch_l in bad:
            btns.append([Button.url(f"➡️ Join {ch_l}", f"https://t.me/{ch_u}")])
        btns.append([Button.inline("✅ Join করেছি — Verify করুন 🔄", "vsub")])

        # ── Custom message: database থেকে প্রথম channel-এর custom_message নাও ──
        custom_msg = ''
        if bad:
            first_ch = bad[0][0]
            c.execute("SELECT custom_message FROM force_channels WHERE username=?", (first_ch,))
            row_msg = c.fetchone()
            if row_msg and row_msg[0] and row_msg[0].strip():
                custom_msg = row_msg[0].strip()

        if custom_msg:
            join_txt = custom_msg
        else:
            join_txt = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔐  **JOIN REQUIRED**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔥 OTP Zone Channel-এ Join করুন\n"
                f"তারপর Verify বাটন চাপুন!\n\n"
                f"📌 Join না করলে বট ব্যবহার করা যাবে না\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔥 *OTP Zone* | Premium OTP Bot"
            )
        await event.respond(join_txt, buttons=btns, parse_mode='md'); return

    lang = glang(uid)
    send_compact_kb(uid,
        (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥  *Welcome to OTP Zone!*  🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎉 *স্বাগতম! আপনাকে স্বাগত জানাই!*\n\n"
        "📲 Unlimited OTP Method চালু আছে\n"
        "💰 প্রতিদিন ৫০০–১০০০ টাকা আয়ের সুযোগ\n\n"
        "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        "✅ WhatsApp  ✅ Telegram  ✅ TikTok\n"
        "✅ Facebook  ✅ Instagram\n\n"
        "👇 নিচের মেনু থেকে শুরু করুন!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 *OTP Zone* | Premium OTP Bot"
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

@bot.on(events.NewMessage(pattern=r'^/setrid (.+) (.+) (.+)$'))
async def on_setrid(event):
    if not is_admin(event.sender_id): return
    short = event.pattern_match.group(1).strip().lower()
    svc   = event.pattern_match.group(2).strip().lower()
    rid   = event.pattern_match.group(3).strip()
    c.execute("INSERT OR REPLACE INTO api_rid_map(short_name,service,rid) VALUES(?,?,?)",
              (short, svc, rid)); db.commit()
    cn, cf = ctry(short)
    await event.respond(f"✅ Live API rid set: {cf} {cn} — {SVC.get(svc,svc)} → `{rid}`", parse_mode='md')

# ════════════════════════════════════════════════════════════
#  /livetest — admin-only real-time API allocation test
#
#  Usage:
#    /livetest <service> <country>   — allocate a number live and report result
#    /livetest status                — ping all 4 API endpoints and show HTTP status
#    /livetest ranges <service>      — list all RIDs /liveaccess returns for a service
#
#  Examples:
#    /livetest telegram uk
#    /livetest whatsapp us
#    /livetest status
#    /livetest ranges telegram
# ════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/livetest(.*)$'))
async def on_livetest(event):
    if not is_admin(event.sender_id): return
    args = (event.pattern_match.group(1) or '').strip().split()

    # ── /livetest status ───────────────────────────────────────────────────────
    if not args or args[0].lower() == 'status':
        await event.respond("⏳ Pinging all 4 API endpoints...", parse_mode='md')
        endpoints = [
            ("POST /getnum",      "post", f"{OTP_API_BASE}/getnum",      {"rid": "test"}),
            ("GET /success-otp",  "get",  f"{OTP_API_BASE}/success-otp", None),
            ("GET /liveaccess",   "get",  f"{OTP_API_BASE}/liveaccess",  None),
            ("GET /console",      "get",  f"{OTP_API_BASE}/console",     None),
        ]
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔌  **2oo9 API Status Test**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ]
        hdr = _api_headers()
        for label, method, url, body in endpoints:
            try:
                if method == "post":
                    r = http_requests.post(url, headers=hdr, json=body, timeout=10)
                else:
                    r = http_requests.get(url, headers=hdr, timeout=10)
                try:
                    payload = r.json()
                    meta_code = (payload or {}).get("meta", {}).get("code", "?")
                except Exception:
                    meta_code = "parse-err"
                icon = "✅" if r.status_code == 200 else "⚠️"
                lines.append(f"{icon} `{label}`\n   HTTP {r.status_code} | meta.code: `{meta_code}`")
            except http_requests.exceptions.Timeout:
                lines.append(f"❌ `{label}`\n   Timeout after 10s")
            except Exception as ex:
                lines.append(f"❌ `{label}`\n   Error: {ex}")
        lines.append(
            "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 API key set: {'✅ Yes' if OTP_API_KEY and OTP_API_KEY != 'YOUR_API_KEY' else '❌ No (placeholder)'}"
        )
        await event.respond("\n\n".join(lines), parse_mode='md')
        return

    # ── /livetest ranges <service> ─────────────────────────────────────────────
    if args[0].lower() == 'ranges':
        svc_filter = args[1].strip().lower() if len(args) > 1 else ''
        await event.respond(f"⏳ Fetching /liveaccess ranges"
                            + (f" for `{svc_filter}`…" if svc_filter else "…"), parse_mode='md')
        services = api_live_services()
        if not services:
            await event.respond("❌ /liveaccess returned no services or API error."); return
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡  **Live Ranges** ({len(services)} total)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ]
        shown = 0
        for entry in services:
            if not isinstance(entry, dict): continue
            e_svc = str(entry.get("service", "") or "").strip().lower()
            if svc_filter and e_svc != svc_filter: continue
            rid     = str(entry.get("rid", "") or "").strip()
            country = str(entry.get("country", "") or "").strip()
            lines.append(f"• svc=`{e_svc}` country=`{country}` rid=`{rid}`")
            shown += 1
            if shown >= 30:
                lines.append(f"_(+{len(services)-shown} more — filter by service to narrow down)_")
                break
        if shown == 0:
            lines.append(f"❌ No ranges found for service `{svc_filter}`.")
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        await event.respond("\n".join(lines), parse_mode='md')
        return

    # ── /livetest otp <number> — watch /success-otp for 60s for a specific number ─
    if args[0].lower() == 'otp':
        if len(args) < 2:
            await event.respond(
                "ℹ️ Usage: `/livetest otp <number>`\n"
                "Example: `/livetest otp +447123456789`\n\n"
                "Polls /success-otp for **60 seconds** and reports every OTP received for that number.",
                parse_mode='md')
            return

        target_raw  = args[1].strip()
        target_norm = re.sub(r'[^\d]', '', target_raw)   # digits only for comparison
        uid_sender  = event.sender_id

        status_msg = await event.respond(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👁  **OTP Watch Active**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📱 Watching: `{target_raw}`\n"
            f"⏱ Duration: 60 seconds\n"
            f"🔄 Polling /success-otp every 2–5 s\n\n"
            f"_Waiting for an OTP…_",
            parse_mode='md')

        import time as _tw, random as _rw

        deadline      = _tw.time() + 60
        found_otps    = []          # [(otp_id, otp_code, raw_msg, elapsed)]
        seen_this_run = set()       # track within this watch session only

        def _watch_poll():
            """Background thread: polls /success-otp until deadline, posts results."""
            nonlocal found_otps
            start = _tw.time()

            while _tw.time() < deadline:
                try:
                    r = http_requests.get(
                        f"{OTP_API_BASE}/success-otp",
                        headers=_api_headers(), timeout=10)
                    payload = r.json() if r.ok else {}
                    otps = (payload.get("data") or {}).get("otps") or []
                    for item in (otps if isinstance(otps, list) else []):
                        if not isinstance(item, dict):
                            continue
                        otp_id  = str(item.get("otp_id", "")).strip()
                        number  = str(item.get("number", "")).strip()
                        message = str(item.get("message", "")).strip()
                        if not otp_id or not number or not message:
                            continue
                        # Match against target number (digits-only comparison)
                        num_norm = re.sub(r'[^\d]', '', number)
                        if target_norm not in num_norm and num_norm not in target_norm:
                            continue
                        if otp_id in seen_this_run:
                            continue
                        seen_this_run.add(otp_id)

                        elapsed = round(_tw.time() - start, 1)
                        # Extract OTP code
                        wa = re.search(r'(?<!\d)(\d{3})-(\d{3})(?!\d)', message)
                        if wa:
                            otp_code = wa.group(1) + wa.group(2)
                        else:
                            kw = re.search(
                                r'(?:code|otp|pin|password|passcode|verification|verif|token|kode)'
                                r'\s*(?:is|:|-|=)?\s*(\d{4,8})(?!\d)',
                                message, re.IGNORECASE)
                            otp_code = kw.group(1) if kw else ''
                            if not otp_code:
                                all_nums = re.findall(r'(?<!\d)(\d{4,8})(?!\d)', message)
                                for length in (6, 5, 4, 7, 8):
                                    for n in all_nums:
                                        if len(n) == length:
                                            otp_code = n
                                            break
                                    if otp_code:
                                        break

                        found_otps.append((otp_id, otp_code, message, number, elapsed))
                        # Live update the status message
                        lines_upd = [
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"✅  **OTP Received!**  ({elapsed}s)\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"📱 Number : `{number}`\n"
                        ]
                        if otp_code:
                            lines_upd.append(f"🔐 OTP     : `{otp_code}`")
                        lines_upd.append(f"💬 Message : `{message[:120]}`")
                        lines_upd.append(f"🆔 otp_id  : `{otp_id}`")
                        lines_upd.append(f"\n_Still watching until timeout…_")
                        try:
                            http_requests.post(
                                f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
                                json={
                                    "chat_id": uid_sender,
                                    "message_id": status_msg.id,
                                    "text": "\n".join(lines_upd),
                                    "parse_mode": "Markdown",
                                }, timeout=8)
                        except Exception:
                            pass
                except Exception:
                    pass
                _tw.sleep(_rw.uniform(2, 5))

            # ── Timeout reached — send final summary ──────────────────────────
            elapsed_total = round(_tw.time() - start, 1)
            if found_otps:
                summary = (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"✅  **OTP Watch Complete** — {len(found_otps)} OTP(s) found in {elapsed_total}s\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                )
                for i, (oid, code, msg, num, ela) in enumerate(found_otps, 1):
                    summary += (
                        f"**#{i}** at {ela}s\n"
                        f"📱 `{num}`\n"
                        f"🔐 OTP: `{code if code else 'not extracted'}`\n"
                        f"💬 `{msg[:100]}`\n\n"
                    )
                summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            else:
                summary = (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏱  **OTP Watch Timeout** — no OTP found in {elapsed_total}s\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📱 Watched: `{target_raw}`\n\n"
                    f"**Possible reasons:**\n"
                    f"• SMS not yet delivered by provider\n"
                    f"• Number not matched in /success-otp response\n"
                    f"• API key issue — try `/livetest status`\n"
                    f"• OTP already seen (otp_id deduplicated)\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
            try:
                http_requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
                    json={
                        "chat_id": uid_sender,
                        "message_id": status_msg.id,
                        "text": summary,
                        "parse_mode": "Markdown",
                    }, timeout=8)
            except Exception:
                http_requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": uid_sender, "text": summary,
                          "parse_mode": "Markdown"}, timeout=8)

        Thread(target=_watch_poll, daemon=True).start()
        return

    # ── /livetest alloc <service> <country> [count] — bulk allocation test ───────
    if args[0].lower() == 'alloc':
        if len(args) < 3:
            await event.respond(
                "ℹ️ Usage: `/livetest alloc <service> <country> [count]`\n"
                "count = 1–5 (default 3)\n\n"
                "Example: `/livetest alloc telegram uk 3`",
                parse_mode='md')
            return

        svc_a   = args[1].strip().lower()
        cty_a   = args[2].strip().lower()
        try:
            count = max(1, min(5, int(args[3]))) if len(args) > 3 else 3
        except ValueError:
            count = 3
        cn_a, cf_a = ctry(cty_a)

        wait_msg = await event.respond(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦  **Bulk Alloc Test**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔧 Service : `{svc_a}`\n"
            f"🌍 Country : {cf_a} `{cty_a.upper()}`\n"
            f"🔢 Requesting : `{count}` numbers\n\n"
            f"_Allocating — please wait…_",
            parse_mode='md')

        import time as _ta
        t0 = _ta.time()
        results = []
        for i in range(count):
            info = api_allocate_live(cty_a, svc_a)
            if info:
                results.append(('✅', info.get('full_number','?'), info.get('operator','?')))
                # Store in premium_stock so bot can serve it
                try:
                    with _db_lock:
                        c.execute(
                            "INSERT OR IGNORE INTO premium_stock"
                            "(country,service,number,status) VALUES(?,?,?,0)",
                            (cty_a, svc_a, info['full_number']))
                        db.commit()
                except Exception:
                    pass
            else:
                results.append(('❌', 'out of stock / API error', ''))
                break   # no point retrying if all RIDs exhausted

        elapsed = round(_ta.time() - t0, 2)
        lines = [
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦  **Bulk Alloc Result** ({elapsed}s)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔧 {svc_a} | {cf_a} {cty_a.upper()} | "
            f"{sum(1 for r in results if r[0]=='✅')}/{count} ok\n"
        ]
        for i, (icon, num, op) in enumerate(results, 1):
            op_str = f"  _{op}_" if op else ""
            lines.append(f"{icon} **#{i}** `{num}`{op_str}")

        if any(r[0] == '✅' for r in results):
            lines.append(
                f"\n✅ Numbers stored in premium_stock — "
                f"users can pick them up via Get Number immediately.")
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        try:
            await bot.edit_message(event.chat_id, wait_msg.id,
                                   "\n".join(lines), parse_mode='md')
        except Exception:
            await event.respond("\n".join(lines), parse_mode='md')
        return

    # ── /livetest <service> <country> — single live allocation test ───────────
    if len(args) < 2:
        await event.respond(
            "ℹ️ **Usage:**\n"
            "`/livetest <service> <country>` — allocate a number live\n"
            "`/livetest alloc <service> <country> [count]` — bulk alloc (1-5)\n"
            "`/livetest status` — ping all API endpoints\n"
            "`/livetest ranges <service>` — list active RIDs\n"
            "`/livetest otp <number>` — watch for OTP delivery (60s)\n\n"
            "**Examples:**\n"
            "`/livetest telegram uk`\n"
            "`/livetest alloc whatsapp us 5`\n"
            "`/livetest otp +447123456789`\n"
            "`/livetest status`",
            parse_mode='md')
        return

    svc_arg   = args[0].strip().lower()
    cty_arg   = args[1].strip().lower()
    cn, cf    = ctry(cty_arg)

    wait_msg = await event.respond(
        f"⏳ Testing live allocation…\n\n"
        f"🔧 Service: `{svc_arg}` | Country: {cf} `{cty_arg.upper()}`\n\n"
        f"_Querying configured RIDs → /liveaccess → trying each RID…_",
        parse_mode='md')

    import time as _t
    t_start = _t.time()
    result  = api_allocate_live(cty_arg, svc_arg)
    elapsed = round(_t.time() - t_start, 2)

    if result:
        num = result.get("full_number", "?")
        op  = result.get("operator", "?")
        rc  = result.get("country", "?")
        txt = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅  **Live Allocation SUCCESS**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📱 Number   › `{num}`\n"
            f"🌍 Country  › `{rc}` {cf}\n"
            f"📡 Operator › `{op}`\n"
            f"⏱ Time     › `{elapsed}s`\n\n"
            f"✅ This number would now appear in Get Number flow.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        # Show what /liveaccess returns so admin can debug
        services = api_live_services()
        matching = [e for e in services if isinstance(e, dict)
                    and str(e.get("service","")).strip().lower() == svc_arg]
        debug_lines = [f"• country=`{e.get('country','')}` rid=`{e.get('rid','')}`"
                       for e in matching[:10]]
        txt = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "❌  **Live Allocation FAILED**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔧 Service: `{svc_arg}` | Country: {cf} `{cty_arg.upper()}`\n"
            f"⏱ Time: `{elapsed}s`\n\n"
            f"**Possible reasons:**\n"
            f"• API key is wrong or not set\n"
            f"• No active ranges for this service+country\n"
            f"• All ranges are currently out of stock\n\n"
            + (f"**Ranges /liveaccess has for `{svc_arg}`** ({len(matching)} found):\n"
               + ("\n".join(debug_lines) if debug_lines else "_None_")
               + "\n\n" if services else "⚠️ /liveaccess returned no data at all.\n\n")
            + "💡 Try `/livetest status` to check API connectivity.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    try:
        await bot.edit_message(event.chat_id, wait_msg.id, txt, parse_mode='md')
    except Exception:
        await event.respond(txt, parse_mode='md')

# ════════════════════════════════════════════════════════════
#  /getnumber command
# ════════════════════════════════════════════════════════════
@bot.on(events.NewMessage(pattern=r'^/getnumber$'))
async def on_getnumber(event):
    if event.is_channel or event.is_group: return
    uid = event.sender_id
    bad = await check_sub(uid)
    if bad:
        await event.respond("❌ আগে channel-এ join করো!", buttons=[
            [Button.url("🔥 Join OTP Zone", OTP_CHANNEL_URL)]]); return
    await bot.send_message(uid,
        "📱 **সার্ভিস সিলেক্ট করুন:**",
        buttons=[
            [Button.inline("💬 WhatsApp","svc_whatsapp"), Button.inline("🔹 Telegram","svc_telegram")],
            [Button.inline("🎵 TikTok",  "svc_tiktok"),  Button.inline("🌐 Facebook","svc_facebook")],
            [Button.inline("📸 Instagram","svc_instagram")]])

# ════════════════════════════════════════════════════════════
#  MESSAGE HANDLER
# ════════════════════════════════════════════════════════════
@bot.on(events.NewMessage())
async def on_msg(event):
    if event.is_channel or event.is_group: return
    uid  = event.sender_id
    text = (event.text or '').strip()
    lang = glang(uid)

    # ── Commands ignore করো — double reply হবে না ──
    if text.startswith("/"): return


    # ── Reply Keyboard Nav Buttons ──────────────────────────────
    if text == "📱 Get Number":
        STATES.pop(uid, None)
        await bot.send_message(uid,
            "📱 **সার্ভিস সিলেক্ট করুন:**",
            buttons=[
                [Button.inline("💬 WhatsApp","svc_whatsapp"), Button.inline("🔹 Telegram","svc_telegram")],
                [Button.inline("🎵 TikTok",  "svc_tiktok"),  Button.inline("🌐 Facebook","svc_facebook")],
                [Button.inline("📸 Instagram","svc_instagram")]]); return

    if text == "🌍 Available Country":
        c.execute("""SELECT a.country_name, a.short_name, a.flag, COUNT(p.id) as cnt
                     FROM active_countries a
                     LEFT JOIN premium_stock p ON p.country=a.short_name AND p.status=0
                     GROUP BY a.short_name ORDER BY a.country_name""")
        rows = c.fetchall()
        if not rows:
            await bot.send_message(uid, "❌ No active countries yet."); return
        txt = "🌍 **Available Countries:**\n\n"
        for cname, cshort, cflag, cnt in rows:
            txt += f"{cflag} {cname} — **{cnt}** numbers\n"
        await bot.send_message(uid, txt, parse_mode='md'); return

    if text == "📋 Active Number":
        c.execute("""SELECT una.number, ps.service, ps.country
                     FROM user_number_assignments una
                     LEFT JOIN premium_stock ps ON REPLACE(REPLACE(ps.number,'+',''),'-','')
                                                 = REPLACE(REPLACE(una.number,'+',''),'-','')
                     WHERE una.user_id=? ORDER BY una.assigned_at DESC LIMIT 10""", (uid,))
        rows = c.fetchall()
        if not rows:
            await bot.send_message(uid, "📊 আপনি এখনো কোনো নাম্বার নেননি।"); return
        txt = "📋 **আপনার Active নাম্বার:**\n\n"
        for num, svc_k, cshort in rows:
            cn, cf = ctry(cshort or ''); srv = SVC.get(svc_k, svc_k or 'Unknown')
            txt += f"{cf} `{num}` — {srv}\n"
        await bot.send_message(uid, txt, parse_mode='md'); return

    if text == "🔍 Search Number":
        STATES[uid] = "search"
        await bot.send_message(uid, "🔍 নাম্বার বা প্রিফিক্স লিখুন:"); return

    if text == "👥 Refer":
        me = await bot.get_me()
        ref_link = f"https://t.me/{me.username}?start=ref_{uid}"
        await bot.send_message(uid,
            f"👥 **রেফার করুন**\n\n🔗 আপনার লিংক:\n`{ref_link}`\n\nবন্ধুদের শেয়ার করুন!",
            parse_mode='md',
            buttons=[[Button.url("🔗 Share ↗", ref_link)]]); return

    if text == "📊 My Status":
        c.execute("SELECT otp_count, numbers_taken FROM history WHERE user_id=? AND date=?", (uid, today()))
        row = c.fetchone(); o = row[0] if row else 0; n = row[1] if row else 0
        c.execute("SELECT COUNT(*) FROM user_number_assignments WHERE user_id=?", (uid,))
        total_nums = c.fetchone()[0]
        otp_bar = PROG(o, max(o,10)); num_bar = PROG(n, max(n,10))
        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤  **আমার স্ট্যাটাস**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 ID: `{uid}`\n\n"
            f"📱 আজ নাম্বার নিয়েছেন: **{n}** টি\n   {num_bar}\n\n"
            f"✅ আজ OTP পেয়েছেন: **{o}** টি\n   {otp_bar}\n\n"
            f"📦 মোট নাম্বার: **{total_nums}** টি\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 *OTP Zone* | Premium OTP Bot"
        )
        await bot.send_message(uid, txt, parse_mode='md'); return
    # ── End Nav Buttons ─────────────────────────────────────────

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
        with _db_lock:
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

    if state == "set_ai_key":
        c.execute("INSERT OR REPLACE INTO bot_settings VALUES('ai_api_key',?)", (text,)); db.commit()
        await event.respond("✅ AI API Key saved!", buttons=[[Button.inline("🔙","adm_ai")]]); return

    if state == "ai":
        ans = ai_reply(text, gset('ai_api_key',''))
        await event.respond(ans + "\n\n_Ask another question or /start_",
                            buttons=[[Button.inline("❌ Exit","adm_ai")]], parse_mode='md')
        STATES[uid] = "ai"; return

    if state == "fch_username":
        raw = text.strip()
        m = re.search(r'(?:t\.me/|@)?([a-zA-Z0-9_]{3,32})$', raw.rstrip('/'))
        uname = m.group(1) if m else raw.lstrip('@').strip()
        if not re.match(r'^[a-zA-Z0-9_]{3,32}$', uname):
            STATES[uid] = "fch_username"   # retry না হারিয়ে যাওয়ার জন্য state রেখে দেওয়া হলো
            await event.respond(
                "❌ সঠিক ফরম্যাট দিন। উদাহরণ: `MyChannel` অথবা `https://t.me/MyChannel`",
                buttons=[[Button.inline("🔙","adm_links")]], parse_mode='md'); return
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

    if state.startswith("fch_custmsg_"):
        ch_u = state[12:]
        if text.strip().lower() == "reset":
            c.execute("UPDATE force_channels SET custom_message='' WHERE username=?", (ch_u,))
            db.commit()
            await event.respond(
                f"✅ @{ch_u} — message default-এ reset হয়েছে।",
                buttons=[[Button.inline("🔗 Links Menu","adm_links")]])
        else:
            c.execute("UPDATE force_channels SET custom_message=? WHERE username=?",
                      (text.strip(), ch_u))
            db.commit()
            await event.respond(
                f"✅ @{ch_u} — Force join message সেট হয়েছে!\n\n"
                f"📝 Preview:\n{text.strip()[:300]}",
                buttons=[[Button.inline("🔗 Links Menu","adm_links")]], parse_mode='md')
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
            f"🔥 *OTP Zone* | Premium OTP Bot"
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
            await event.answer("❌ এখনো Join করোনি!", alert=True); return
        await event.answer("✅ Verified! Welcome to OTP Zone!", alert=False)
        await event.delete()
        send_compact_kb(uid,
            "🔥 *Welcome to OTP Zone!* ✅\n\n"
            + ("📲 Unlimited Method Active\n💰 Earn 500-1000 BDT daily"
               if lang=='en' else
               "📲 Unlimited Method চালু\n💰 প্রতিদিন ৫০০-১০০০ টাকা আয় করুন"),
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
            f"🔥 *OTP Zone* | Premium OTP Bot"
        )
        await event.edit(txt, buttons=adm_kb(), parse_mode='md'); return

    if data == "view_user":
        await event.delete()
        send_compact_kb(uid,
            "🔥 *Welcome to OTP Zone!* ✅\n\n"
            + ("📲 Unlimited Method Active\n💰 Earn 500-1000 BDT daily"
               if lang=='en' else "📲 Unlimited Method চালু\n💰 প্রতিদিন ৫০০-১০০০ টাকা আয় করুন"),
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
            f"🔥 *OTP Zone* | Premium OTP Bot"
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
        # Countries with existing local stock
        c.execute("SELECT DISTINCT p.country FROM premium_stock p "
                  "JOIN active_countries a ON a.short_name=p.country "
                  "WHERE p.service=? AND p.status=0", (svc,))
        stocked = {r[0] for r in c.fetchall()}
        # All active countries (even without local stock — live allocation covers them)
        c.execute("SELECT short_name FROM active_countries")
        all_active = {r[0] for r in c.fetchall()}
        ws = stocked | all_active  # union: show every active country
        if not ws:
            await event.edit(
                f"❌ No active countries configured.\n"
                f"Admin → 🌍 Countries → activate at least one country.",
                buttons=[[Button.inline("◀️ Back","select_svc")]]); return
        btns = []; row = []
        for short in sorted(ws):
            cn, cf = ctry(short)
            nm = cn[:8] if len(cn)>8 else cn
            label = f"{cf} {nm} [{short.upper()}]"
            row.append(Button.inline(label, f"ctry_{svc}_{short}"))
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
        txt += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 *OTP Zone* | Premium OTP Bot"
        await event.edit(txt, buttons=[[Button.inline("🔙 ফিরে যান","adm_back")]], parse_mode='md'); return

    if data == "adm_daily":
        td = today()
        c.execute("SELECT COUNT(*) FROM otp_log WHERE received_at LIKE ?", (f"{td}%",))
        total_otp = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM otp_log WHERE received_at LIKE ? AND matched=1", (f"{td}%",))
        matched_otp = c.fetchone()[0]
        c.execute("SELECT SUM(numbers_taken) FROM history WHERE date=?", (td,))
        total_nums = c.fetchone()[0] or 0
        c.execute("SELECT SUM(otp_count) FROM history WHERE date=?", (td,))
        total_otp_users = c.fetchone()[0] or 0

        # ── Match rate for today ──
        match_pct = round(matched_otp / total_otp * 100) if total_otp > 0 else 0
        match_bar = PROG(match_pct, 100, 12)

        # ── 7-day match rate history ──
        history_7 = []
        for d_offset in range(6, -1, -1):
            day = str(datetime.date.today() - datetime.timedelta(days=d_offset))
            c.execute("SELECT COUNT(*) FROM otp_log WHERE received_at LIKE ?", (f"{day}%",))
            d_total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM otp_log WHERE received_at LIKE ? AND matched=1", (f"{day}%",))
            d_match = c.fetchone()[0]
            d_pct = round(d_match / d_total * 100) if d_total > 0 else 0
            short_day = day[5:]  # MM-DD
            history_7.append((short_day, d_total, d_match, d_pct))

        c.execute("""SELECT user_id, numbers_taken, otp_count FROM history
                     WHERE date=? ORDER BY numbers_taken DESC LIMIT 10""", (td,))
        user_rows = c.fetchall()
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈  **DAILY REPORT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 তারিখ › **{td}**\n\n"
            f"📥 মোট OTP এসেছে     › {STATUS(total_otp, 1)}\n"
            f"✅ ম্যাচড OTP         › {STATUS(matched_otp, 1)}\n"
            f"📱 মোট নাম্বার নেওয়া › {STATUS(total_nums, 1)}\n"
            f"👤 ইউজারদের OTP      › {STATUS(total_otp_users, 1)}\n\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"📊 **আজকের Match Rate:**\n"
            f"{match_bar} **{match_pct}%**\n\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"📆 **৭ দিনের Match Rate:**\n\n"
        )
        for short_day, d_total, d_match, d_pct in history_7:
            bar = PROG(d_pct, 100, 8)
            marker = " ◄ আজ" if short_day == td[5:] else ""
            txt += f"`{short_day}` {bar} **{d_pct}%** ({d_match}/{d_total}){marker}\n"

        txt += (
            f"\n┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"🏆 **আজকের টপ ইউজার:**\n\n"
        )
        if user_rows:
            for i, (u_id, u_nums, u_otp) in enumerate(user_rows, 1):
                medal = medals[i-1] if i <= len(medals) else f"{i}."
                txt += f"{medal} `{u_id}`\n   📱 {u_nums} নাম্বার | ✅ {u_otp} OTP\n\n"
        else:
            txt += "⚠️ আজ কোনো অ্যাক্টিভিটি নেই।"
        txt += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔥 *OTP Zone* | Premium OTP Bot"
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
        # custom_message সহ fetch করো
        c.execute("SELECT username, label, custom_message FROM force_channels ORDER BY id")
        chs_full = c.fetchall()
        txt = (f"🔗 **Links & Force Channels**\n\n"
               f"📢 OTP Link: {glink('otp_group')}\n\n"
               f"🔒 **Force Channels** ({len(chs)}/10):\n")
        for row_fc in chs_full:
            u, l = row_fc[0], row_fc[1]
            cm = row_fc[2] if len(row_fc) > 2 else ''
            has_msg = "✏️" if cm and cm.strip() else "➕"
            txt += f"• {l} — @{u}  {has_msg}msg\n"
        btns = [
            [Button.inline("✏️ OTP Link","edit_otp")],
            [Button.inline("➕ Add Force Channel","add_fch")],
        ]
        for row_fc in chs_full:
            ch_u, ch_l = row_fc[0], row_fc[1]
            btns.append([
                Button.inline(f"✏️ Msg: {ch_l}", f"editmsg_{ch_u}"),
                Button.inline(f"❌ Remove @{ch_u}", f"rmfch_{ch_u}"),
            ])
        btns.append([Button.inline("🔙","adm_back")])
        await event.edit(txt, buttons=btns, parse_mode='md'); return

    if data == "edit_otp":
        STATES[uid] = "otp_link"
        await event.edit("✏️ Send new OTP group link:", buttons=[[Button.inline("🔙","adm_links")]]); return

    if data == "add_fch":
        chs = get_force_channels()
        if len(chs) >= 10:
            await event.answer("❌ Max 10 channels reached!", alert=True); return
        STATES[uid] = "fch_username"
        await event.edit(
            "➕ **Add Force Channel/Group**\n\nSend the @username (without @):\nExample: `MyChannel`",
            buttons=[[Button.inline("🔙","adm_links")]], parse_mode='md'); return

    if data.startswith("editmsg_"):
        ch_u = data[8:]
        c.execute("SELECT label, custom_message FROM force_channels WHERE username=?", (ch_u,))
        row_em = c.fetchone()
        ch_lbl = row_em[0] if row_em else ch_u
        cur_msg = (row_em[1] or '').strip() if row_em else ''
        STATES[uid] = f"fch_custmsg_{ch_u}"
        preview = f"\n\n📝 **বর্তমান message:**\n{cur_msg[:200]}" if cur_msg else "\n\n_(এখনো কোনো custom message সেট নেই)_"
        await event.edit(
            f"✏️ **Force Join Message Edit**\n\n"
            f"Channel: {ch_lbl} (@{ch_u}){preview}\n\n"
            f"নতুন message টাইপ করুন বা 'reset' পাঠান default-এ ফেরাতে:\n"
            f"_(Markdown supported: **bold**, _italic_, `code`)_",
            buttons=[[Button.inline("🔙 বাতিল","adm_links")]], parse_mode='md'); return

    if data.startswith("rmfch_"):
        ch_u = data[6:]
        c.execute("DELETE FROM force_channels WHERE username=?", (ch_u,)); db.commit()
        await event.answer(f"✅ @{ch_u} removed!", alert=False)
        chs = get_force_channels()
        txt = (f"🔗 **Links & Force Channels**\n\n"
               f"📢 OTP Link: {glink('otp_group')}\n\n"
               f"🔒 **Force Channels** ({len(chs)}/10):\n")
        for u, l in chs:
            txt += f"• {l} — @{u}\n"
        btns = [
            [Button.inline("✏️ OTP Link","edit_otp")],
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
        # 2oo9 API — read-only status view, no user input required
        try:
            r = http_requests.get(f"{OTP_API_BASE}/success-otp", headers=_api_headers(), timeout=8)
            api_status = f"✅ **Online** (HTTP {r.status_code})"
            try:
                payload = r.json()
                meta = (payload or {}).get("meta", {})
                if meta.get("code") == 200:
                    otps = (payload.get("data") or {}).get("otps") or []
                    api_status += f"\n📩 Last poll: **{len(otps)}** OTP পাওয়া গেছে"
                else:
                    api_status += f"\n⚠️ meta.code: `{meta.get('code')}`"
            except Exception:
                api_status += "\n⚠️ Response parse করা যায়নি"
        except Exception:
            api_status = "❌ **Offline / সংযোগ ব্যর্থ**"

        c.execute("SELECT COUNT(*) FROM otp_log"); total_logs = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM otp_log WHERE received_at LIKE ?", (f"{today()}%",))
        today_logs = c.fetchone()[0]

        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡  **OTP API স্ট্যাটাস**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔑 API Key: `(hardcoded — header: mauthapi)`\n"
            f"🌐 Endpoint: `api.2oo9.cloud`\n"
            f"⏱ Poll interval: প্রতি **৫ সেকেন্ড** (/success-otp)\n\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
            f"📶 **সংযোগ স্ট্যাটাস:**\n{api_status}\n\n"
            f"📥 আজ OTP এসেছে   › **{today_logs}** টি\n"
            f"📦 মোট OTP লগ     › **{total_logs}** টি\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 *OTP Zone* | Premium OTP Bot"
        )
        await event.edit(txt, buttons=[[Button.inline("🔙 ফিরে যান","adm_back")]], parse_mode='md'); return

    if data == "adm_otp_log":
        c.execute(
            "SELECT phone, message, sender, received_at, matched "
            "FROM otp_log ORDER BY id DESC LIMIT 20"
        )
        rows = c.fetchall()
        c.execute("SELECT COUNT(*) FROM otp_log"); total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM otp_log WHERE matched=1"); matched_total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM otp_log WHERE received_at LIKE ?", (f"{today()}%",))
        today_cnt = c.fetchone()[0]

        txt = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋  **OTP লগ** (সর্বশেষ ২০ টি)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📦 মোট লগ: **{total}**  |  ✅ ম্যাচ: **{matched_total}**  |  📅 আজ: **{today_cnt}**\n\n"
            f"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n\n"
        )
        if rows:
            for phone_v, msg_v, sender_v, recv_v, matched_v in rows:
                status = "✅" if matched_v else "❌"
                # trim timestamp to HH:MM:SS
                ts = str(recv_v)[11:19] if recv_v and len(str(recv_v)) >= 19 else str(recv_v)
                short_msg = str(msg_v)[:30] + "…" if msg_v and len(str(msg_v)) > 30 else (msg_v or '—')
                txt += (
                    f"{status} `{phone_v}`\n"
                    f"   💬 `{short_msg}`\n"
                    f"   🏢 {sender_v or '—'}  ⏱ {ts}\n\n"
                )
        else:
            txt += "⚠️ এখনো কোনো OTP লগ নেই।\n"

        txt += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✅ = ম্যাচ হয়েছে  |  ❌ = কোনো ইউজার মেলেনি"
        await event.edit(txt, buttons=[
            [Button.inline("🗑 লগ পরিষ্কার করুন","otp_log_clear")],
            [Button.inline("🔙 ফিরে যান","adm_back")]
        ], parse_mode='md'); return

    if data == "otp_log_clear":
        if uid != SUPER_ADMIN:
            await event.answer("❌ শুধু Super Admin পারবেন।", alert=True); return
        c.execute("DELETE FROM otp_log"); db.commit()
        await event.answer("✅ OTP লগ পরিষ্কার হয়ে গেছে!", alert=False)
        await event.edit(
            "🗑 **OTP লগ মুছে ফেলা হয়েছে।**\n\nসব এন্ট্রি ডিলিট হয়ে গেছে।",
            buttons=[[Button.inline("🔙 ফিরে যান","adm_back")]], parse_mode='md'); return

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
                caption=f"💻 **OTP Zone Bot Code**\n📅 {today()}\n📏 Complete — always up to date!",
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
    await bot.start(bot_token=BOT_TOKEN)
    me = await bot.get_me()
    _BOT_USERNAME_CACHE["v"] = me.username
    print("Bot online")
    await set_commands()
    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())