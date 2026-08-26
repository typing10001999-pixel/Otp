"""
Telegram OTP number bot

Focused replacement for the previous bot:
  /start -> force-join check -> main menu -> service -> automatic allocation
  -> number display -> prefix / OTP refresh

Secrets are intentionally loaded only from environment variables.  The bot
uses Telethon because that is the framework used by the existing application.
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiohttp
from aiohttp import web
from telethon import Button, TelegramClient, events, functions
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommand, BotCommandScopeDefault


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def env_int(name: str, default: int = 0) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except ValueError:
        return default


API_ID = env_int("API_ID")
API_HASH = os.getenv("API_HASH", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = env_int("ADMIN_ID")
API_BASE_URL = os.getenv("API_BASE_URL", "").strip().rstrip("/")
API_KEY = os.getenv("API_KEY", "").strip()
PORT = env_int("PORT", 10000)
OTP_POLL_INTERVAL = max(10, env_int("OTP_POLL_INTERVAL", 20))

configured_db = os.getenv("DB_PATH", "").strip()
if configured_db:
    DB_PATH = Path(configured_db)
else:
    # A Render persistent disk is normally mounted at /data.  Fall back to
    # the application directory for local development.
    DB_PATH = Path("/data/bot.sqlite3") if Path("/data").is_dir() else Path("bot.sqlite3")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("otp-bot")

if not (API_ID and API_HASH and BOT_TOKEN and ADMIN_ID):
    raise RuntimeError("API_ID, API_HASH, BOT_TOKEN, and ADMIN_ID must be set")


# ---------------------------------------------------------------------------
# Persistent storage
# ---------------------------------------------------------------------------

db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.row_factory = sqlite3.Row
db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA busy_timeout=5000")

db.executescript(
    """
    CREATE TABLE IF NOT EXISTS bot_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS bot_users (
        user_id INTEGER PRIMARY KEY,
        first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        added_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS services (
        service_key TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS api_ranges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_key TEXT NOT NULL,
        country TEXT NOT NULL DEFAULT '',
        rid TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 100,
        UNIQUE(service_key, country, rid)
    );

    CREATE TABLE IF NOT EXISTS premium_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country TEXT NOT NULL DEFAULT '',
        service TEXT NOT NULL,
        number TEXT NOT NULL UNIQUE,
        status INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        service_key TEXT NOT NULL,
        country TEXT NOT NULL DEFAULT '',
        number TEXT NOT NULL,
        operator TEXT NOT NULL DEFAULT '',
        source TEXT NOT NULL,
        assigned_at TEXT NOT NULL,
        prefix TEXT NOT NULL DEFAULT '',
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE INDEX IF NOT EXISTS idx_allocations_user
        ON allocations(user_id, assigned_at DESC);
    CREATE INDEX IF NOT EXISTS idx_allocations_number
        ON allocations(number);
    CREATE UNIQUE INDEX IF NOT EXISTS idx_allocations_user_number
        ON allocations(user_id, number);

    CREATE TABLE IF NOT EXISTS processed_otps (
        otp_key TEXT PRIMARY KEY,
        number TEXT NOT NULL,
        received_at TEXT NOT NULL,
        user_sent INTEGER NOT NULL DEFAULT 0,
        channel_sent INTEGER NOT NULL DEFAULT 0
    );
    """
)

# Migrate the old api_ranges table if it came from the uploaded application.
existing_columns = {
    row["name"] for row in db.execute("PRAGMA table_info(api_ranges)").fetchall()
}
if "service" in existing_columns and "service_key" not in existing_columns:
    db.execute("ALTER TABLE api_ranges ADD COLUMN service_key TEXT")
    db.execute("UPDATE api_ranges SET service_key=service WHERE service_key IS NULL")
if "country" not in existing_columns:
    db.execute("ALTER TABLE api_ranges ADD COLUMN country TEXT NOT NULL DEFAULT ''")
if "rid" not in existing_columns:
    db.execute("ALTER TABLE api_ranges ADD COLUMN rid TEXT NOT NULL DEFAULT ''")
if "priority" not in existing_columns:
    db.execute("ALTER TABLE api_ranges ADD COLUMN priority INTEGER NOT NULL DEFAULT 100")

user_columns = {
    row["name"] for row in db.execute("PRAGMA table_info(bot_users)").fetchall()
}
if "first_seen" not in user_columns:
    db.execute("ALTER TABLE bot_users ADD COLUMN first_seen TEXT NOT NULL DEFAULT ''")
if "last_seen" not in user_columns:
    db.execute("ALTER TABLE bot_users ADD COLUMN last_seen TEXT NOT NULL DEFAULT ''")

# Preserve assignments from the previous application when its database is
# reused.  Old assignments did not carry service metadata, so infer it from
# the old stock row where possible.
if db.execute(
    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_number_assignments'"
).fetchone():
    db.execute(
        """
        INSERT OR IGNORE INTO allocations
            (user_id,service_key,country,number,operator,source,assigned_at)
        SELECT
            old.user_id,
            COALESCE(stock.service, 'unknown'),
            COALESCE(stock.country, ''),
            CASE
                WHEN substr(old.number, 1, 1)='+' THEN old.number
                ELSE '+' || old.number
            END,
            '',
            'legacy',
            old.assigned_at
        FROM user_number_assignments AS old
        LEFT JOIN premium_stock AS stock
          ON REPLACE(REPLACE(REPLACE(stock.number, '+', ''), '-', ''), ' ', '') =
             REPLACE(REPLACE(REPLACE(old.number, '+', ''), '-', ''), ' ', '')
        """
    )
    db.execute(
        """
        UPDATE premium_stock
        SET status=1
        WHERE EXISTS (
            SELECT 1 FROM user_number_assignments AS old
            WHERE REPLACE(REPLACE(REPLACE(premium_stock.number, '+', ''), '-', ''), ' ', '') =
                  REPLACE(REPLACE(REPLACE(old.number, '+', ''), '-', ''), ' ', '')
        )
        """
    )

DEFAULT_SERVICES = (
    ("whatsapp", "💬 WhatsApp"),
    ("telegram", "🔹 Telegram"),
    ("tiktok", "🎵 TikTok"),
    ("facebook", "🌐 Facebook"),
    ("instagram", "📸 Instagram"),
)
for service_key, label in DEFAULT_SERVICES:
    db.execute(
        "INSERT OR IGNORE INTO services(service_key,label,enabled) VALUES(?,?,1)",
        (service_key, label),
    )
db.execute(
    "INSERT OR IGNORE INTO admins(user_id,added_at) VALUES(?,?)",
    (ADMIN_ID, datetime.now(timezone.utc).isoformat()),
)
for key, value in (
    ("description", "Choose a service to receive an available number."),
    ("force_channel", ""),
    ("force_channel_url", ""),
    ("otp_channel", ""),
):
    db.execute(
        "INSERT OR IGNORE INTO bot_settings(key,value) VALUES(?,?)",
        (key, value),
    )
db.commit()


def get_setting(key: str, default: str = "") -> str:
    row = db.execute("SELECT value FROM bot_settings WHERE key=?", (key,)).fetchone()
    return str(row["value"]) if row else default


def set_setting(key: str, value: str) -> None:
    db.execute(
        "INSERT INTO bot_settings(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    db.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID or db.execute(
        "SELECT 1 FROM admins WHERE user_id=?", (user_id,)
    ).fetchone() is not None


def remember_user(user_id: int) -> None:
    now = now_iso()
    db.execute(
        "INSERT INTO bot_users(user_id,first_seen,last_seen) VALUES(?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET last_seen=excluded.last_seen",
        (user_id, now, now),
    )
    db.commit()


# ---------------------------------------------------------------------------
# Formatting and validation
# ---------------------------------------------------------------------------

COUNTRY_NAMES = {
    "bd": ("Bangladesh", "🇧🇩"),
    "gb": ("United Kingdom", "🇬🇧"),
    "uk": ("United Kingdom", "🇬🇧"),
    "us": ("United States", "🇺🇸"),
    "ca": ("Canada", "🇨🇦"),
    "au": ("Australia", "🇦🇺"),
    "in": ("India", "🇮🇳"),
    "pk": ("Pakistan", "🇵🇰"),
    "ng": ("Nigeria", "🇳🇬"),
    "za": ("South Africa", "🇿🇦"),
}


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=False)


def normalize_number(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def format_number(value: Any) -> str:
    raw = str(value or "").strip()
    digits = normalize_number(raw)
    return f"+{digits}" if digits else raw


def valid_number(value: Any) -> bool:
    return 6 <= len(normalize_number(value)) <= 15


def mask_number(value: str) -> str:
    digits = normalize_number(value)
    if len(digits) <= 4:
        return format_number(value)
    return f"+{digits[:-4]}XXXX"


def country_display(country: str) -> tuple[str, str]:
    return COUNTRY_NAMES.get(
        country.lower().strip(), (country.upper() or "Unknown", "🌍")
    )


def service_label(service_key: str) -> str:
    row = db.execute(
        "SELECT label FROM services WHERE service_key=?", (service_key,)
    ).fetchone()
    return str(row["label"]) if row else service_key.title()


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

http_session: Optional[aiohttp.ClientSession] = None


def api_root() -> str:
    if not API_BASE_URL:
        return ""
    if API_BASE_URL.endswith("/@public/api"):
        return API_BASE_URL
    return f"{API_BASE_URL}/@public/api"


async def api_request(
    method: str, path: str, payload: Optional[dict[str, Any]] = None
) -> Optional[dict[str, Any]]:
    if not (api_root() and API_KEY and http_session):
        return None
    url = f"{api_root()}/{path.lstrip('/')}"
    headers = {"mauthapi": API_KEY, "Accept": "application/json"}
    try:
        async with http_session.request(
            method, url, headers=headers, json=payload, allow_redirects=False
        ) as response:
            if response.status < 200 or response.status >= 300:
                log.warning("Number API returned HTTP %s for %s", response.status, path)
                return None
            body = await response.json(content_type=None)
            return body if isinstance(body, dict) else {"data": body}
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        log.warning("Number API temporarily unavailable for %s", path)
        return None


def response_code(body: Optional[dict[str, Any]]) -> int:
    try:
        return int((body or {}).get("meta", {}).get("code", 0))
    except (TypeError, ValueError):
        return 0


def data_object(body: dict[str, Any]) -> dict[str, Any]:
    value = body.get("data", {})
    return value if isinstance(value, dict) else {}


async def allocate_from_api(
    service_key: str,
) -> Optional[dict[str, str]]:
    ranges = db.execute(
        "SELECT country,rid FROM api_ranges WHERE service_key=? ORDER BY priority,id",
        (service_key,),
    ).fetchall()
    for row in ranges:
        body = await api_request("POST", "/getnum", {"rid": str(row["rid"])})
        code = response_code(body)
        if code == 2946:  # documented out-of-stock response
            continue
        if code != 200 or not body:
            continue
        data = data_object(body)
        number = (
            data.get("full_number")
            or data.get("number")
            or data.get("phone")
            or body.get("full_number")
        )
        if not valid_number(number):
            continue
        return {
            "number": format_number(number),
            "country": str(data.get("country") or row["country"] or ""),
            "operator": str(data.get("operator") or data.get("carrier") or ""),
            "source": "api",
        }
    return None


def allocate_from_local(user_id: int, service_key: str) -> Optional[dict[str, str]]:
    # Claim the row in a transaction so two users cannot receive the same
    # local number during concurrent callbacks.
    try:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT id,country,number FROM premium_stock "
            "WHERE service=? AND status=0 ORDER BY id LIMIT 1",
            (service_key,),
        ).fetchone()
        if not row:
            db.rollback()
            return None
        changed = db.execute(
            "UPDATE premium_stock SET status=1 WHERE id=? AND status=0",
            (row["id"],),
        ).rowcount
        if changed != 1:
            db.rollback()
            return None
        db.commit()
        return {
            "number": format_number(row["number"]),
            "country": str(row["country"] or ""),
            "operator": "",
            "source": "local",
        }
    except sqlite3.Error:
        db.rollback()
        log.exception("Could not claim local number")
        return None


async def allocate_number(user_id: int, service_key: str) -> Optional[int]:
    allocation = await allocate_from_api(service_key)
    if allocation is None:
        allocation = allocate_from_local(user_id, service_key)
    if allocation is None:
        return None
    cur = db.execute(
        "INSERT INTO allocations(user_id,service_key,country,number,operator,source,assigned_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (
            user_id,
            service_key,
            allocation["country"],
            allocation["number"],
            allocation["operator"],
            allocation["source"],
            now_iso(),
        ),
    )
    db.commit()
    return int(cur.lastrowid)


def allocation_for_user(user_id: int, allocation_id: int) -> Optional[sqlite3.Row]:
    return db.execute(
        "SELECT * FROM allocations WHERE id=? AND user_id=?",
        (allocation_id, user_id),
    ).fetchone()


# ---------------------------------------------------------------------------
# OTP processing
# ---------------------------------------------------------------------------

def otp_items(body: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    if not body:
        return []
    data = body.get("data", body)
    if isinstance(data, dict):
        for key in ("otps", "success_otp", "items", "results"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def otp_fields(item: dict[str, Any]) -> tuple[str, str, str, str]:
    number = str(
        item.get("number")
        or item.get("phone")
        or item.get("full_number")
        or item.get("sim")
        or ""
    )
    message = str(
        item.get("message")
        or item.get("sms")
        or item.get("text")
        or item.get("otp")
        or item.get("code")
        or ""
    ).strip()
    sender = str(item.get("sender") or item.get("from") or item.get("app") or "Unknown")
    item_id = str(item.get("id") or item.get("otp_id") or "").strip()
    if not item_id:
        item_id = hashlib.sha256(
            f"{normalize_number(number)}|{sender}|{message}".encode()
        ).hexdigest()
    return normalize_number(number), message, sender, item_id


async def deliver_otp(
    number: str, message: str, sender: str, item_id: str
) -> bool:
    allocation = db.execute(
        "SELECT * FROM allocations WHERE REPLACE(number,'+','')=? "
        "ORDER BY assigned_at DESC LIMIT 1",
        (number,),
    ).fetchone()
    if not allocation or not message:
        return False

    otp_key = f"{item_id}:{number}"
    inserted = db.execute(
        "INSERT OR IGNORE INTO processed_otps(otp_key,number,received_at) VALUES(?,?,?)",
        (otp_key, number, now_iso()),
    ).rowcount
    db.commit()
    if inserted != 1:
        return False

    country, flag = country_display(allocation["country"])
    label = service_label(allocation["service_key"])
    user_text = (
        "🔐 <b>OTP received</b>\n\n"
        f"Service: {esc(label)}\n"
        f"Number: <code>{esc(allocation['number'])}</code>\n"
        f"Country: {esc(flag)} {esc(country)}\n"
        f"Sender: {esc(sender)}\n\n"
        f"<code>{esc(message)}</code>"
    )
    try:
        await bot.send_message(allocation["user_id"], user_text, parse_mode="html")
        db.execute(
            "UPDATE processed_otps SET user_sent=1 WHERE otp_key=?", (otp_key,)
        )
        db.commit()
    except Exception:
        log.warning("Could not deliver OTP to its owner")

    channel = get_setting("otp_channel").strip()
    if channel:
        channel_text = (
            "📥 <b>OTP received</b>\n\n"
            f"Service: {esc(label)}\n"
            f"Number: <code>{esc(mask_number(allocation['number']))}</code>\n"
            f"OTP: <code>{esc(message)}</code>\n"
            f"Time: {esc(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}"
        )
        try:
            await bot.send_message(channel, channel_text, parse_mode="html")
            db.execute(
                "UPDATE processed_otps SET channel_sent=1 WHERE otp_key=?", (otp_key,)
            )
            db.commit()
        except Exception:
            log.warning("Could not forward OTP to configured channel")
    else:
        db.execute(
            "UPDATE processed_otps SET channel_sent=1 WHERE otp_key=?", (otp_key,)
        )
        db.commit()
    return True


async def check_for_user_otps(user_id: int) -> int:
    body = await api_request("GET", "/success-otp")
    if response_code(body) not in (0, 200):
        return 0
    allocations = db.execute(
        "SELECT number FROM allocations WHERE user_id=? AND active=1", (user_id,)
    ).fetchall()
    owned_numbers = {normalize_number(row["number"]) for row in allocations}
    delivered = 0
    for item in otp_items(body):
        number, message, sender, item_id = otp_fields(item)
        if number in owned_numbers and await deliver_otp(number, message, sender, item_id):
            delivered += 1
    return delivered


async def otp_poller() -> None:
    while True:
        try:
            if API_BASE_URL and API_KEY:
                body = await api_request("GET", "/success-otp")
                if response_code(body) in (0, 200):
                    for item in otp_items(body):
                        number, message, sender, item_id = otp_fields(item)
                        # deliver_otp performs the strict allocation ownership
                        # check before anything is sent.
                        if number and message:
                            await deliver_otp(number, message, sender, item_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("OTP polling cycle failed")
        await asyncio.sleep(OTP_POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Force join and UI
# ---------------------------------------------------------------------------

states: dict[int, str] = {}


def force_channel() -> str:
    return get_setting("force_channel").strip()


def force_join_url() -> str:
    configured = get_setting("force_channel_url").strip()
    if configured:
        return configured
    channel = force_channel()
    if channel.startswith("@"):
        return f"https://t.me/{channel[1:]}"
    return ""


async def is_channel_member(user_id: int) -> bool:
    channel = force_channel()
    if not channel:
        return True
    try:
        entity = await bot.get_entity(int(channel) if channel.lstrip("-").isdigit() else channel)
        participant = await bot.get_input_entity(user_id)
        result = await bot(functions.channels.GetParticipantRequest(entity, participant))
        kind = type(result.participant).__name__.lower()
        return "left" not in kind and "banned" not in kind
    except Exception:
        # A bot must be able to see channel members (usually by being an
        # administrator).  Fail closed so unverified users cannot continue.
        return False


def force_join_buttons() -> list[list[Any]]:
    rows: list[list[Any]] = []
    url = force_join_url()
    if url:
        rows.append([Button.url("📢 Join required channel", url)])
    rows.append([Button.inline("✅ Check / Verify", b"force_verify")])
    return rows


async def show_force_join(event: Any, edit: bool = False) -> None:
    text = (
        "🔒 <b>Channel membership required</b>\n\n"
        "Join the channel below, then tap <b>Check / Verify</b> to continue."
    )
    if edit:
        await event.edit(text, buttons=force_join_buttons(), parse_mode="html")
    else:
        await event.respond(text, buttons=force_join_buttons(), parse_mode="html")


def main_menu_buttons(user_id: int) -> list[list[Any]]:
    rows = [[Button.inline("📱 Get Number", b"get_number")]]
    rows.append([Button.inline("🔐 Check OTP", b"check_otp")])
    if is_admin(user_id):
        rows.append([Button.inline("⚙️ Admin Settings", b"admin")])
    return rows


async def user_has_access(user_id: int) -> bool:
    if is_admin(user_id):
        return True
    return await is_channel_member(user_id)


async def show_main(event: Any, user_id: int, edit: bool = False) -> None:
    if not await user_has_access(user_id):
        await show_force_join(event, edit=edit)
        return
    description = get_setting("description").strip() or "Choose a service to receive a number."
    text = f"📲 <b>Welcome</b>\n\n{esc(description)}"
    if edit:
        await event.edit(text, buttons=main_menu_buttons(user_id), parse_mode="html")
    else:
        await event.respond(text, buttons=main_menu_buttons(user_id), parse_mode="html")


async def show_services(event: Any, user_id: int) -> None:
    rows = db.execute(
        "SELECT service_key,label FROM services WHERE enabled=1 ORDER BY rowid"
    ).fetchall()
    buttons: list[list[Any]] = []
    pair: list[Any] = []
    for row in rows:
        pair.append(Button.inline(str(row["label"]), f"svc:{row['service_key']}".encode()))
        if len(pair) == 2:
            buttons.append(pair)
            pair = []
    if pair:
        buttons.append(pair)
    buttons.append([Button.inline("◀️ Back", b"main")])
    text = "📱 <b>Select a service</b>\n\nThe bot will choose an available range automatically."
    await event.edit(text, buttons=buttons, parse_mode="html")


async def show_allocation(event: Any, user_id: int, allocation_id: int) -> None:
    row = allocation_for_user(user_id, allocation_id)
    if not row:
        await event.answer("Number not found.", alert=True)
        return
    country, flag = country_display(row["country"])
    prefix = row["prefix"]
    display = f"{prefix}{row['number']}" if prefix else row["number"]
    operator = f"\nOperator: {esc(row['operator'])}" if row["operator"] else ""
    text = (
        "✅ <b>Number allocated</b>\n\n"
        f"Service: {esc(service_label(row['service_key']))}\n"
        f"Number: <code>{esc(display)}</code>\n"
        f"Country: {esc(flag)} {esc(country)}{operator}\n"
        f"Source: {esc(row['source'])}\n\n"
        "A prefix changes only the display in this bot; it never changes the API allocation."
    )
    buttons = [
        [
            Button.inline("🔄 Refresh OTP", f"otp:{allocation_id}".encode()),
            Button.inline("➕ Add Prefix", f"prefix:{allocation_id}".encode()),
        ],
        [
            Button.inline("📱 Get Another", f"another:{row['service_key']}".encode()),
            Button.inline("◀️ Main Menu", b"main"),
        ],
    ]
    await event.edit(text, buttons=buttons, parse_mode="html")


def admin_buttons() -> list[list[Any]]:
    return [
        [Button.inline("✏️ Bot Description", b"adm:description")],
        [Button.inline("🔒 Force-Join Channel", b"adm:force")],
        [Button.inline("📤 OTP Forwarding Channel", b"adm:otp")],
        [Button.inline("🌐 API Base URL", b"adm:api")],
        [Button.inline("📱 Services", b"adm:services"), Button.inline("🔢 Ranges", b"adm:ranges")],
        [Button.inline("👤 User Menu", b"main")],
    ]


async def show_admin(event: Any, edit: bool = True) -> None:
    if edit:
        await event.edit(
            "⚙️ <b>Admin Settings</b>\n\n"
            "Secrets stay in Render environment variables. "
            "Normal bot configuration can be changed here.",
            buttons=admin_buttons(),
            parse_mode="html",
        )
    else:
        await event.respond(
            "⚙️ <b>Admin Settings</b>",
            buttons=admin_buttons(),
            parse_mode="html",
        )


# ---------------------------------------------------------------------------
# Admin configuration screens
# ---------------------------------------------------------------------------

async def show_services_admin(event: Any) -> None:
    rows = db.execute(
        "SELECT service_key,label,enabled FROM services ORDER BY rowid"
    ).fetchall()
    text = "📱 <b>Services</b>\n\n"
    buttons: list[list[Any]] = []
    for row in rows:
        state = "✅" if row["enabled"] else "⚪"
        text += f"{state} {esc(row['label'])} — <code>{esc(row['service_key'])}</code>\n"
        buttons.append(
            [Button.inline(f"{state} Toggle {row['service_key']}", f"toggle_svc:{row['service_key']}".encode())]
        )
    buttons.append([Button.inline("➕ Add Service", b"add_service")])
    buttons.append([Button.inline("◀️ Back", b"admin")])
    await event.edit(text, buttons=buttons, parse_mode="html")


async def show_ranges_admin(event: Any) -> None:
    rows = db.execute(
        "SELECT service_key,country,rid FROM api_ranges ORDER BY service_key,priority,id"
    ).fetchall()
    text = "🔢 <b>API Range Mappings</b>\n\n"
    buttons: list[list[Any]] = []
    for row in rows:
        text += (
            f"<code>{esc(row['service_key'])}</code> / "
            f"<code>{esc(row['country'] or 'any')}</code> → "
            f"<code>{esc(row['rid'])}</code>\n"
        )
        buttons.append(
            [Button.inline(
                f"❌ Remove {row['service_key']} {row['country'] or 'any'}",
                f"remove_range:{row['service_key']}:{row['country']}:{row['rid']}".encode(),
            )]
        )
    if not rows:
        text += "No mappings configured. API allocation will not run until a range is added."
    buttons += [
        [Button.inline("➕ Add Range", b"add_range")],
        [Button.inline("◀️ Back", b"admin")],
    ]
    await event.edit(text, buttons=buttons, parse_mode="html")


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

bot = TelegramClient("otp_bot", API_ID, API_HASH)


async def set_commands() -> None:
    await bot(
        SetBotCommandsRequest(
            scope=BotCommandScopeDefault(),
            lang_code="",
            commands=[
                BotCommand("start", "Open the bot"),
                BotCommand("admin", "Admin settings"),
            ],
        )
    )


@bot.on(events.NewMessage(pattern=r"^/start(?:\s+.*)?$"))
async def on_start(event: Any) -> None:
    if event.is_group or event.is_channel:
        return
    user_id = event.sender_id
    remember_user(user_id)
    await show_main(event, user_id, edit=False)


@bot.on(events.NewMessage(pattern=r"^/admin$"))
async def on_admin_command(event: Any) -> None:
    if event.is_group or event.is_channel:
        return
    if is_admin(event.sender_id):
        await show_admin(event, edit=False)


@bot.on(events.NewMessage())
async def on_message(event: Any) -> None:
    if event.is_group or event.is_channel or not event.sender_id:
        return
    user_id = event.sender_id
    state = states.pop(user_id, "")
    text = (event.raw_text or "").strip()
    if not state or not text:
        return

    if state.startswith("prefix:"):
        if not await user_has_access(user_id):
            await show_force_join(event)
            return
        if len(text) > 32 or "\n" in text or "\r" in text or any(ord(c) < 32 for c in text):
            await event.respond("❌ Prefix must be plain text up to 32 characters.")
            return
        allocation_id = int(state.split(":", 1)[1])
        if allocation_for_user(user_id, allocation_id):
            db.execute(
                "UPDATE allocations SET prefix=? WHERE id=? AND user_id=?",
                (text, allocation_id, user_id),
            )
            db.commit()
            await event.respond("✅ Prefix saved. It affects display only.")
        return

    if not is_admin(user_id):
        return

    if state == "description":
        if len(text) > 3500:
            await event.respond("❌ Description is limited to 3500 characters.")
        else:
            set_setting("description", text)
            await event.respond("✅ Bot description updated.")
        return

    if state == "force":
        if text.lower() in {"off", "disable", "disabled", "none"}:
            set_setting("force_channel", "")
            set_setting("force_channel_url", "")
            await event.respond("✅ Force-join disabled.")
        else:
            parts = [part.strip() for part in text.split("|", 1)]
            channel = parts[0]
            if not (channel.startswith("@") or channel.lstrip("-").isdigit()):
                await event.respond("❌ Use @channel, -100... or `off`.")
                return
            set_setting("force_channel", channel)
            set_setting("force_channel_url", parts[1] if len(parts) == 2 else "")
            await event.respond(
                "✅ Force-join saved. The bot must be able to inspect channel members."
            )
        return

    if state == "otp":
        if text.lower() in {"off", "disable", "disabled", "none"}:
            set_setting("otp_channel", "")
            await event.respond("✅ OTP forwarding disabled.")
        elif text.startswith("@") or text.lstrip("-").isdigit():
            set_setting("otp_channel", text)
            await event.respond("✅ OTP forwarding channel saved.")
        else:
            await event.respond("❌ Use @channel, -100... or `off`.")
        return

    if state == "api_base":
        # Kept as a defensive branch for states left by an older process.
        await event.respond(
            "ℹ️ API_BASE_URL and API_KEY are managed in Render environment "
            "variables. Use the Ranges screen to configure rids."
        )
        return

    if state == "add_service":
        parts = [part.strip() for part in text.split("|", 1)]
        if len(parts) != 2 or not re.fullmatch(r"[a-z0-9_-]{2,32}", parts[0]):
            await event.respond("❌ Format: `service_key | Display Label`.")
            return
        db.execute(
            "INSERT INTO services(service_key,label,enabled) VALUES(?,?,1) "
            "ON CONFLICT(service_key) DO UPDATE SET label=excluded.label,enabled=1",
            (parts[0].lower(), parts[1][:64]),
        )
        db.commit()
        await event.respond("✅ Service saved.")
        return

    if state == "add_range":
        parts = text.split()
        if len(parts) != 3 or not re.fullmatch(r"[a-z0-9_-]{2,32}", parts[0]):
            await event.respond("❌ Format: `service_key country_code rid`.")
            return
        db.execute(
            "INSERT OR IGNORE INTO api_ranges(service_key,country,rid,priority) VALUES(?,?,?,100)",
            (parts[0].lower(), parts[1].lower(), parts[2]),
        )
        db.commit()
        await event.respond("✅ API range mapping saved.")
        return


@bot.on(events.CallbackQuery)
async def on_callback(event: Any) -> None:
    user_id = event.sender_id
    data = event.data.decode("utf-8", "ignore")

    if data == "force_verify":
        await event.answer("Checking membership…")
        await show_main(event, user_id, edit=True)
        return

    if data == "main":
        await event.answer()
        await show_main(event, user_id, edit=True)
        return

    if data == "admin":
        if not is_admin(user_id):
            await event.answer("Admin only.", alert=True)
            return
        await event.answer()
        await show_admin(event)
        return

    if data == "get_number":
        if not await user_has_access(user_id):
            await event.answer("Join the required channel first.", alert=True)
            await show_force_join(event, edit=True)
            return
        await event.answer()
        await show_services(event, user_id)
        return

    if data == "check_otp":
        if not await user_has_access(user_id):
            await event.answer("Join the required channel first.", alert=True)
            await show_force_join(event, edit=True)
            return
        await event.answer("Checking OTP…")
        count = await check_for_user_otps(user_id)
        await event.respond(
            f"✅ {count} new OTP(s) found." if count else "⏳ No new OTP found yet."
        )
        return

    if data.startswith("svc:") or data.startswith("another:"):
        if not await user_has_access(user_id):
            await event.answer("Join the required channel first.", alert=True)
            await show_force_join(event, edit=True)
            return
        service_key = data.split(":", 1)[1]
        service = db.execute(
            "SELECT 1 FROM services WHERE service_key=? AND enabled=1", (service_key,)
        ).fetchone()
        if not service:
            await event.answer("Service unavailable.", alert=True)
            return
        await event.answer("Finding an available number…")
        allocation_id = await allocate_number(user_id, service_key)
        if allocation_id is None:
            await event.edit(
                f"❌ No available number for {esc(service_label(service_key))}.",
                buttons=[[Button.inline("◀️ Back to Services", b"get_number")]],
                parse_mode="html",
            )
            return
        await show_allocation(event, user_id, allocation_id)
        return

    if data.startswith("otp:"):
        allocation_id = int(data.split(":", 1)[1])
        row = allocation_for_user(user_id, allocation_id)
        if not row:
            await event.answer("Number not found.", alert=True)
            return
        await event.answer("Checking OTP…")
        count = await check_for_user_otps(user_id)
        await show_allocation(event, user_id, allocation_id)
        if not count:
            await event.answer("No new OTP yet.", alert=False)
        return

    if data.startswith("prefix:"):
        allocation_id = int(data.split(":", 1)[1])
        if not allocation_for_user(user_id, allocation_id):
            await event.answer("Number not found.", alert=True)
            return
        states[user_id] = f"prefix:{allocation_id}"
        await event.answer()
        await event.respond("✏️ Send the display prefix (max 32 characters).")
        return

    if data.startswith("adm:"):
        if not is_admin(user_id):
            await event.answer("Admin only.", alert=True)
            return
        option = data.split(":", 1)[1]
        prompts = {
            "description": ("description", "Send the new bot description."),
            "force": ("force", "Send @channel, -100... [optional join URL], or `off`."),
            "otp": ("otp", "Send @channel, -100..., or `off`."),
            "api": ("api_base", "API_BASE_URL is an environment variable; send a URL to see the setup note."),
            "services": (None, ""),
            "ranges": (None, ""),
        }
        if option == "services":
            await show_services_admin(event)
            return
        if option == "ranges":
            await show_ranges_admin(event)
            return
        if option == "api":
            base_status = esc(api_root() or "not configured")
            key_status = "configured" if API_KEY else "not configured"
            await event.answer()
            await event.edit(
                "🌐 <b>Number API configuration</b>\n\n"
                f"Base URL: <code>{base_status}</code>\n"
                f"API key: <b>{key_status}</b>\n\n"
                "API_BASE_URL and API_KEY are secrets/configuration managed "
                "in Render environment variables. API range mappings are "
                "configured below.",
                buttons=[
                    [Button.inline("🔢 Manage Ranges", b"adm:ranges")],
                    [Button.inline("◀️ Back", b"admin")],
                ],
                parse_mode="html",
            )
            return
        state, prompt = prompts[option]
        states[user_id] = state
        await event.answer()
        await event.edit(prompt, buttons=[[Button.inline("◀️ Cancel", b"admin")]], parse_mode="html")
        return

    if data == "add_service":
        if not is_admin(user_id):
            await event.answer("Admin only.", alert=True)
            return
        states[user_id] = "add_service"
        await event.edit(
            "➕ Send: `service_key | Display Label`\nExample: `signal | 🔵 Signal`",
            buttons=[[Button.inline("◀️ Cancel", b"adm:services")]],
            parse_mode="html",
        )
        return

    if data == "add_range":
        if not is_admin(user_id):
            await event.answer("Admin only.", alert=True)
            return
        states[user_id] = "add_range"
        await event.edit(
            "➕ Send: `service_key country_code rid`\n"
            "The bot tries mappings in priority order and never asks users to choose a range.",
            buttons=[[Button.inline("◀️ Cancel", b"adm:ranges")]],
            parse_mode="html",
        )
        return

    if data.startswith("toggle_svc:"):
        if not is_admin(user_id):
            await event.answer("Admin only.", alert=True)
            return
        service_key = data.split(":", 1)[1]
        db.execute(
            "UPDATE services SET enabled=CASE enabled WHEN 1 THEN 0 ELSE 1 END WHERE service_key=?",
            (service_key,),
        )
        db.commit()
        await event.answer("Updated.")
        await show_services_admin(event)
        return

    if data.startswith("remove_range:"):
        if not is_admin(user_id):
            await event.answer("Admin only.", alert=True)
            return
        _, service_key, country, rid = data.split(":", 3)
        db.execute(
            "DELETE FROM api_ranges WHERE service_key=? AND country=? AND rid=?",
            (service_key, country, rid),
        )
        db.commit()
        await event.answer("Removed.")
        await show_ranges_admin(event)
        return

    await event.answer()


# ---------------------------------------------------------------------------
# Render health endpoint and optional webhook
# ---------------------------------------------------------------------------

async def health(_: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)


async def webhook_otp(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except (json.JSONDecodeError, ValueError):
        payload = dict(await request.post())
    if not isinstance(payload, dict):
        return web.Response(text="invalid payload", status=400)
    number, message, sender, item_id = otp_fields(payload)
    if not number or not message:
        return web.Response(text="missing number or message", status=400)
    await deliver_otp(number, message, sender, item_id)
    return web.Response(text="OK", status=200)


async def start_health_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/alive", health)
    app.router.add_post("/webhook/otp", webhook_otp)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    return runner


async def main() -> None:
    global http_session
    timeout = aiohttp.ClientTimeout(total=15)
    http_session = aiohttp.ClientSession(timeout=timeout)
    health_runner = await start_health_server()
    poll_task = asyncio.create_task(otp_poller())
    try:
        await bot.start(bot_token=BOT_TOKEN)
        await set_commands()
        log.info("Bot is online; health server listening on port %s", PORT)
        await bot.run_until_disconnected()
    finally:
        poll_task.cancel()
        await asyncio.gather(poll_task, return_exceptions=True)
        await health_runner.cleanup()
        if http_session:
            await http_session.close()


if __name__ == "__main__":
    asyncio.run(main())