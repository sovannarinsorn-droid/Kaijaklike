"""
╔══════════════════════════════════════════════════════════════╗
║     Kaijaklike Bot — カイロゼン SMM  [v11]                ║
║     SMM Panel · ដាក់លុយ CamRapidPay KHQR                   ║
║     Panel Admin · បន្ថែម/កាត់ Balance                       ║
║     Compatible: Python 3.10+ · Termux / Render / VPS       ║
║     v10: /newbot — បង្កើត Bot ថ្មីដោយផ្ទាល់ខាងក្នុង Telegram  ║
║          /mybots — គ្រប់គ្រង Bot រងទាំងអស់ (start/stop/del)  ║
╚══════════════════════════════════════════════════════════════╝
ដំឡើង:
  pip install pyTelegramBotAPI requests flask qrcode pillow --break-system-packages
"""

import json, logging, time, re, threading, io, os, sys, subprocess, datetime
import requests as http_req
from dotenv import load_dotenv
load_dotenv()
import telebot
from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton as _KB_orig,
    InlineKeyboardMarkup, InlineKeyboardButton as _IKB_orig
)
import re as _re

# ── Colored / Premium-emoji buttons (Telegram Bot API 9.4+) ───────────────
# Injects 'style' + 'icon_custom_emoji_id' into JSON so any pyTelegramBotAPI
# version works, regardless of whether the installed lib already knows them.
#
# ⚠️ សំខាន់ (រកឃើញនិងកែនៅ 2026-08-06): Telegram Bot API 9.4 កំណត់ត្រឹមតែ
#    field ឈ្មោះ "style" ប៉ុណ្ណោះ (មិនមែន "color" ទេ) ហើយតម្លៃត្រូវជា
#    "danger" (ក្រហម) | "primary" (ខៀវ) | "success" (បៃតង) ប៉ុណ្ណោះ។
#    កូដចាស់ប្រើ field ឈ្មោះ "color" ខុស + តម្លៃប្រឌិតឡើងផ្ទាល់ខ្លួន
#    ("active"/"inactive"/"progress") ដែល Telegram មិនស្គាល់ទាល់តែសោះ —
#    មានន័យថា ពណ៌ button មិនដែលដំណើរការជាក់ស្តែងទេ តាំងពីដើមមក។
#    _COLOR_MAP ខាងក្រោមបកប្រែឈ្មោះ semantic ចាស់ (ប្រើពាសពេញកូដរាប់រយកន្លែង)
#    ទៅជាតម្លៃ enum ត្រឹមត្រូវ ដោយមិនចាំបាច់កែ call site ណាមួយឡើយ។
_COLOR_MAP = {
    "active":   "success",   # បៃតង — action ធម្មតា/ជ្រើសរើសបាន
    "progress": "primary",   # ខៀវ — highlighted / ជំហានបន្ទាប់ / custom
    "danger":   "danger",    # ក្រហម — លុប/បដិសេធ (បើប្រើផ្ទាល់)
    "inactive": None,        # គ្មាន style ពិសេស — មើលទៅដូច button ធម្មតា
    "default":  None,
}
def _to_style(color):
    if not color:
        return None
    return _COLOR_MAP.get(color, color if color in ("danger", "primary", "success") else None)
# គំនិត: លែងត្រូវចងចាំ "semantic key" ដូចមុនទៀតហើយ (account/topup/...) —
# ឥឡូវ key គឺជា emoji unicode character ពិតដែលប្រើក្នុង bot (👤 💸 🛒 ...).
# តម្លៃ = custom_emoji_id (premium) បើកំណត់រួច, None = មិនទាន់មាន → fallback
# ទៅ unicode emoji ធម្មតា។ EMOJI_MAP គ្របដណ្តប់គ្រប់ jang emoji ដែលប្រើក្នុង
# ⇒ reply-keyboard buttons, inline buttons, និង អត្ថបទសារ (message text) ទាំងអស់។
# របៀបកំណត់: /setemojis (reply ទៅសារណាមួយមាន premium emoji, លំដាប់ណាក៏បាន —
# bot ស្គាល់ automatically តាម emoji ធម្មតាដែលនៅក្រោម premium icon នីមួយៗ)
# ចំណាំ: កុំកសាង list នេះឡើងវិញដោយ iterate លើ string តែមួយបន្ត — flag emoji
# (🇰🇭 ។ល។) និង variation-selector emoji (✏️ ។ល។) មាន 2 code points/តួ ដូច្នេះ
# ត្រូវសរសេរជា element ដាច់ពីគ្នាក្នុង list ដូចខាងក្រោម ដើម្បីកុំឲ្យខូច។
_EMOJI_CHAR_LIST = [
    '🇰🇭', '🇬🇧', '🇺🇸', '❌', '✅', '💰', '→', '👤', '📊', '💳',
    '✏️', '📋', '💸', '⚠️', '🚫', '💡', '📝', '🗑️', '👥', '❤️',
    '👁️', '🔗', '🛒', '🔍', '💬', '🔢', '🎟️', '📂', '📦', '💔',
    '🔄', '🔑', '💵', '🌐', '🙏', '📢', '🤖', '😊', '⚙️', '🔙',
    '💙', '➕', '✍️', '🔔', '🎵', '📱', '🟢', '🔴', '🛑', '✕',
    '👈', '🏠', '🎉', '📌', '💹', '🧪', '🐦', '👋', '👇', '❓',
    '🖼️', '📘', '📸', '⚡', '📭', '📞', '🔖', '👜', '🙍', '🛠️',
    '★', '🎁', '🧵', '👀', '😍', '🛡️', '📏', '📎', '🔓', '⬅️',
    '✨', '➡️', '🔌', '🔵', '🟡', '📤', '🔕', '📁', '🚀', '←',
    '⏱', '🆔', '▶️',
]
EMOJI_MAP = {ch: None for ch in _EMOJI_CHAR_LIST}
# ធ្វើ regex pattern មួយសម្រាប់ចាប់ emoji នៅដើម string (រួមទាំង variation
# selector ﻿(\uFE0F) និង flag ២-តួ) ដើម្បីប្រើក្នុងការ auto-detect ខាងក្រោម។
_EMOJI_CHARS_SORTED = sorted(EMOJI_MAP.keys(), key=len, reverse=True)
_LEADING_EMOJI_RE = _re.compile(
    "^(" + "|".join(_re.escape(c) for c in _EMOJI_CHARS_SORTED) + ")"
)

def _leading_emoji(s):
    """បើ string ចាប់ផ្ដើមដោយ emoji ណាមួយក្នុង EMOJI_MAP សូមត្រឡប់តួនោះមកវិញ។"""
    if not s or not isinstance(s, str):
        return None
    m = _LEADING_EMOJI_RE.match(s)
    return m.group(1) if m else None

def _strip_leading_emoji_text(text, ch):
    """ដកចេញ emoji ធម្មតា (ch) ពីដើម text បើ icon_custom_emoji_id ត្រូវបានប្រើ
    ជំនួសរួចហើយ — បើមិនដូច្នេះទេ Telegram នឹងបង្ហាញទាំង icon premium (មុន
    button) ព្រមទាំង emoji ធម្មតា (ក្នុង label) ក្នុងពេលតែមួយ ដែលមើលទៅដូចស្ទួន។"""
    if not text or not isinstance(text, str) or not ch:
        return text
    if text.startswith(ch):
        return text[len(ch):].lstrip()
    return text

class InlineKeyboardButton(_IKB_orig):
    def __init__(self, *args, color: str = None, emoji_id: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._color = color
        label = kwargs.get("text") if "text" in kwargs else (args[0] if args else None)
        self._emoji_char = _leading_emoji(label)
        if emoji_id is None and self._emoji_char:
            emoji_id = EMOJI_MAP.get(self._emoji_char)
        self._emoji_id = emoji_id

    def to_dict(self):
        d = super().to_dict()
        style = _to_style(self._color)
        if style:
            d["style"] = style
        if self._emoji_id:
            d["icon_custom_emoji_id"] = str(self._emoji_id)
            if "text" in d:
                d["text"] = _strip_leading_emoji_text(d["text"], self._emoji_char)
        return d

# ⚠️ កំណត់ត្រា (កែនៅ 2026-08-06 លើកទី ២): ការយល់ដឹងមុននេះខុស — Telegram
#    Bot API 9.4 ពិតជា support "icon_custom_emoji_id" + "style" លើ
#    KeyboardButton (reply keyboard) ដែរ ដូចគ្នានឹង InlineKeyboardButton
#    (មើល core.telegram.org/bots/api → KeyboardButton object). មូលហេតុពិត
#    ដែល emoji premium មិនបង្ហាញ គឺ to_dict() ចាស់ **មិនដែលដាក់ field នេះ
#    ចូល JSON ទាល់តែសោះ**។
#    ⚠️ លក្ខខណ្ឌចាំបាច់ពី Telegram: bot owner ត្រូវមាន Telegram Premium
#    សកម្ម (ឬ bot ទិញ additional username លើ Fragment) មិនដូច្នេះទេ
#    Telegram នឹងមិនបង្ហាញ icon នេះឡើយ ទោះកូដត្រឹមត្រូវក៏ដោយ។
#
#    ឥឡូវនេះកូដខាងក្រោមកាត់ emoji unicode ចេញពី text ដូច InlineKeyboardButton
#    ដែរ (ដើម្បីកុំឲ្យស្ទួន icon+emoji) ប៉ុន្ដែ ដើម្បីកុំឲ្យ button ធ្លាក់ចូល
#    fallback ("មិនស្គាល់ button") នៅពេល Telegram ត្រឡប់ text ដែលកាត់រួច
#    មកវិញ, យើងកត់ត្រា mapping "text ដែលកាត់ → text ដើម (មាន emoji)" ក្នុង
#    _STRIPPED_TEXT_MAP ។ MAIN MESSAGE HANDLER ត្រូវ restore text ដើមវិញ
#    មុននឹង match លក្ខខណ្ឌ text == / text in (...) ណាមួយ (មើល "# ── Restore
#    stripped-emoji text ──" ក្នុង handle_msg)។
_STRIPPED_TEXT_MAP = {}

class KeyboardButton(_KB_orig):
    """Reply-keyboard button ដែលអាចដាក់ premium emoji icon បាន (user-side only)."""
    def __init__(self, *args, color: str = None, emoji_id: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._color = color
        label = kwargs.get("text") if "text" in kwargs else (args[0] if args else None)
        self._emoji_char = _leading_emoji(label)
        if emoji_id is None and self._emoji_char:
            emoji_id = EMOJI_MAP.get(self._emoji_char)
        self._emoji_id = emoji_id

    def to_dict(self):
        d = super().to_dict()
        style = _to_style(self._color)
        if style:
            d["style"] = style
        if self._emoji_id and "text" in d:
            original_text = d["text"]
            d["icon_custom_emoji_id"] = str(self._emoji_id)
            stripped = _strip_leading_emoji_text(original_text, self._emoji_char)
            if stripped != original_text:
                # កត់ត្រា mapping ដើម្បីឲ្យ handler ចាស់ៗនៅតែដំណើរការធម្មតា
                _STRIPPED_TEXT_MAP[stripped] = original_text
                d["text"] = stripped
        return d

# ─────────────────────────────────────────────────────────────────────────
from flask import Flask, request as flask_request, jsonify
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── Auto-install deps ───
def _ensure_deps():
    pkgs = {"PIL": "pillow", "qrcode": "qrcode", "numpy": "numpy"}
    for mod, pkg in pkgs.items():
        try: __import__(mod)
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg,
                            "--break-system-packages", "-q"], check=False)
_ensure_deps()

import qrcode
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
#  ╔═══════════════════════════════════════════════════════╗
#  ║   🛠️  SETUP — បំពេញព័ត៌មាននៅទីនេះ មុនដំណើរការ bot   ║
#  ╚═══════════════════════════════════════════════════════╝
#
#  ដើម្បីដំណើរការ bot ច្រើនច្បាប់ក្នុងពេលតែមួយ៖
#    1) ចម្លងឯកសារនេះទាំងមូល ដាក់ក្នុង folder ថ្មីដាច់ដោយឡែក
#       (ឧ. bot_shop2/kaijaklike_bot.py)
#    2) ប្តូរតម្លៃខាងក្រោម (BOT_TOKEN, ADMIN_ID, CAMRAPID_API_KEY,
#       CONTROL_PORT) ឱ្យខុសគ្នាពី bot ដទៃ
#    3) ដំណើរការដោយ `python3 kaijaklike_bot.py` ដាច់ដោយឡែក
#       ក្នុង terminal/session ផ្សេង (ឬ tmux/screen ផ្សេងគ្នា)
#    ⚠️ សារសំខាន់: CONTROL_PORT ត្រូវតែខុសគ្នារាល់ bot មួយៗ
#       ដែលដំណើរការក្នុងម៉ាស៊ីនតែមួយ បើមិនដូច្នេះ bot ទីពីរនឹង
#       crash ដោយសារ port ប៉ះគ្នា (bot ទីមួយប្រើ 5056 default)
#
#  អាចបំពេញផ្ទាល់ខាងក្រោម ឬកំណត់ជា environment variable
#  (env var នឹងមានអទិភាពជាង តម្លៃ default ខាងក្រោម)
# ═══════════════════════════════════════════════════════════
BOT_TOKEN          = os.getenv("BOT_TOKEN", "")   # 👈 Bot Token ពី @BotFather — កំណត់ជា Environment Variable ប៉ុណ្ណោះ (កុំសរសេរផ្ទាល់ក្នុងកូដ)
ADMIN_ID           = int(os.getenv("ADMIN_ID", "0"))                                    # 👈 Telegram ID អ្នកគ្រប់គ្រង bot នេះ
INSTANCE_NAME      = os.getenv("INSTANCE_NAME", "")          # មិនទទេ = នេះជា bot រងដែលត្រូវបាន /newbot បង្កើត
IS_MASTER          = (INSTANCE_NAME == "")                    # bot ដើម (ដែលអ្នករត់ដោយផ្ទាល់) = master, អាចបង្កើត /newbot
BOT_DISPLAY_NAME   = os.getenv("BOT_DISPLAY_NAME", "")             # ឈ្មោះ bot ដែលបង្ហាញដល់អ្នកប្រើ (ប្តូរបានពី /newbot)
BOT_WELCOME_MSG    = os.getenv("BOT_WELCOME_MSG", "")              # welcome message custom (ទទេ = ប្រើ default)

# ── CamRapidPay — Create KHQR + Check transaction ──
CAMRAPID_API_KEY   = os.getenv("CAMRAPID_API_KEY", "")   # 👈 CamRapidPay API Key — កំណត់ជា Environment Variable ប៉ុណ្ណោះ
CAMRAPID_CREATE    = "https://pay.camrapidpay.com/api/v1/khqr/create-payments"
CAMRAPID_CHECK     = "https://pay.camrapidpay.com/check-transaction-api"
WEBHOOK_URL        = os.getenv("WEBHOOK_URL", "")          # ដាក់ URL webhook (optional)

DEPOSIT_EXPIRE_SEC = 300   # 5 minutes (CamRapidPay expire 5 min)
POLL_INTERVAL      = 8

# Flask Control Server
# សុវត្ថិភាព: បើមិនកំណត់ CONTROL_KEY ជា env var ទេ បង្កើត key ចៃដន្យ (មិនប្រើ default
# ដែលគេទាយបាន "change_this_secret" ទៀត) ដើម្បីការពារ /shutdown /restart /broadcast_web
import secrets as _secrets
_CONTROL_KEY_ENV = os.getenv("CONTROL_KEY", "")
if not _CONTROL_KEY_ENV:
    CONTROL_KEY = _secrets.token_urlsafe(24)
    logger.warning(
        "⚠️ CONTROL_KEY មិនបានកំណត់ក្នុង Environment Variable! "
        "បង្កើត key ចៃដន្យបណ្តោះអាសន្នជំនួស (នឹងផ្លាស់ប្តូររាល់ restart): %s "
        "→ សូមកំណត់ CONTROL_KEY ជា env var នៅ Render ដើម្បីឲ្យ key ថេរ។", CONTROL_KEY)
else:
    CONTROL_KEY = _CONTROL_KEY_ENV
CONTROL_PORT       = int(os.getenv("CONTROL_PORT", "5056"))   # 👈 ប្តូរ port នេះបើដំណើរការ bot ច្រើនច្បាប់ក្នុងម៉ាស៊ីនតែមួយ (5056, 5057, 5058...)

# ── Startup guard — ការពារកុំឲ្យ deploy ដោយគ្មាន credential សំខាន់ៗ ──────────
if __name__ == "__main__" and not INSTANCE_NAME:
    _missing = []
    if not BOT_TOKEN:  _missing.append("BOT_TOKEN")
    if not ADMIN_ID:   _missing.append("ADMIN_ID")
    if _missing:
        sys.exit(
            "❌ ខ្វះ Environment Variable ចាំបាច់: " + ", ".join(_missing) +
            "\nសូមកំណត់ក្នុង Render → Environment (កុំដាក់ផ្ទាល់ក្នុងកូដ)។"
        )

# ═══════════════════════════════════════════════════════════
#  FILES  (all persisted on Render Disk so redeploy/restart never wipes data)
# ═══════════════════════════════════════════════════════════
DATA_DIR        = os.environ.get("DATA_DIR", "/var/data")
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    DATA_DIR = "."   # fallback ក្នុងករណី disk មិនមាន (local/Termux test)

def _dpath(name):
    return os.path.join(DATA_DIR, name)

WALLETS_FILE    = _dpath("smm_wallets.json")
USERS_FILE      = _dpath("smm_users.json")
LANG_FILE       = _dpath("smm_lang.json")
PROMO_FILE      = _dpath("smm_promos.json")
SETTINGS_FILE   = _dpath("smm_settings.json")
NOTIFY_FILE     = _dpath("smm_notify.json")

SMM_API_FILE    = _dpath("smm_api.json")
SMM_SVC_FILE    = _dpath("smm_services.json")
SMM_ORD_FILE    = _dpath("smm_orders.json")
SMM_PROFIT_FILE = _dpath("smm_profit.json")
SMM_POLL_FILE   = _dpath("smm_poll.json")
SMM_DEP_FILE    = _dpath("smm_deposits.json")
DEP_BONUS_FILE  = _dpath("smm_deposit_bonus.json")
SUB_ADMIN_FILE  = _dpath("smm_sub_admins.json")
SUPPORT_CFG_FILE= _dpath("smm_support.json")
CAMRAPID_CFG_FILE= _dpath("smm_camrapid.json")
EMOJI_FILE      = _dpath("smm_emoji.json")

def _load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def _save(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e: logger.error(f"Save {path}: {e}")

# ─── Load all state ───
# EMOJI_MAP ត្រូវបានកំណត់ default (None) ខាងលើ — ឥឡូវ merge ជាមួយតម្លៃ
# ដែលធ្លាប់រក្សាទុកនៅក្នុងឯកសារ (បើមាន) ដើម្បីឲ្យ /setemojis រក្សាទុកជាអចិន្ត្រៃយ៍
_EMOJI_DEFAULTS = dict(EMOJI_MAP)
EMOJI_MAP.update(_load(EMOJI_FILE, {}))
EMOJI_KEYS = list(_EMOJI_DEFAULTS.keys())   # បញ្ជី emoji ទាំងអស់ដែល bot ស្គាល់ (សម្រាប់ reference)

wallets      = _load(WALLETS_FILE,   {})
users_db     = _load(USERS_FILE,     {})
user_lang    = _load(LANG_FILE,      {})
promos       = _load(PROMO_FILE,     {})
settings     = _load(SETTINGS_FILE,  {})
notify_cfg   = _load(NOTIFY_FILE,    {"channel_id": "-1003930705105", "enabled": True})

smm_api      = _load(SMM_API_FILE,   {"url": "", "key": ""})
smm_services = _load(SMM_SVC_FILE,   {})
smm_orders   = _load(SMM_ORD_FILE,   {})
smm_profit   = _load(SMM_PROFIT_FILE,{"pct": 20})
smm_poll     = _load(SMM_POLL_FILE,  {"interval": POLL_INTERVAL})
smm_deps     = _load(SMM_DEP_FILE,   {})

# ── Auto Deposit Bonus — "ដាក់ $1 ឡើងទៅ ទទួល 5% ត្រលប់មកវិញ" ──────────
# enabled: បើក/បិទ Auto Bonus, min_amount: ចំនួនអប្បបរមាដែលទទួលបាន Bonus,
# pct: ភាគរយ Bonus (គិតលើចំនួនប្រាក់ដែលដាក់)។ កែបានពី Admin Menu → 🎁 Bonus ដាក់លុយ
dep_bonus_cfg = _load(DEP_BONUS_FILE, {"enabled": True, "min_amount": 1.0, "pct": 5.0})

# ── Auto-seed TikTok Promote Khmer packages ──
_TIKTOK_PACKAGES = [
    {
        "slug":        "manual_tiktok_promote_p1",
        "label":       "🇰🇭 500-1k ❤️ · 1.8k 👁 View",
        "description": "500-1K Likes ❤️ + 1.8K Views 👁\n⏱ 5-15 នាទី",
        "flat_price":  0.99,
    },
    {
        "slug":        "manual_tiktok_promote_p2",
        "label":       "🇰🇭 1k-2k ❤️ · 3.5k 👁 View",
        "description": "1K-2K Likes ❤️ + 3.5K Views 👁\n⏱ 5-15 នាទី",
        "flat_price":  1.99,
    },
    {
        "slug":        "manual_tiktok_promote_p3",
        "label":       "🇰🇭 2k-3k ❤️ · 10k 👁 View",
        "description": "2K-3K Likes ❤️ + 10K Views 👁\n⏱ 10-20 នាទី",
        "flat_price":  3.25,
    },
    {
        "slug":        "manual_tiktok_promote_p4",
        "label":       "🇰🇭 3k-5k ❤️ · 20k 👁 View",
        "description": "3K-5K Likes ❤️ + 20K Views 👁\n⏱ 15-30 នាទី",
        "flat_price":  5.49,
    },
    {
        "slug":        "manual_tiktok_promote_p5",
        "label":       "🇰🇭 500 ❤️ · 1k 👁 · 100 👤 Follow",
        "description": "500 Likes ❤️ + 1K Views 👁 + 100 Followers 👤\n⏱ 5-15 នាទី",
        "flat_price":  1.99,
    },
    {
        "slug":        "manual_tiktok_promote_view1",
        "label":       "🇰🇭 2k-5k 👁 View",
        "description": "2K-5K Views 👁 (View ណាមួយ)\n⏱ 5-15 នាទី",
        "flat_price":  0.99,
    },
    {
        "slug":        "manual_tiktok_promote_view2",
        "label":       "🇰🇭 5k-10k 👁 View",
        "description": "5K-10K Views 👁 (View ណាមួយ)\n⏱ 5-15 នាទី",
        "flat_price":  1.99,
    },
    {
        "slug":        "manual_tiktok_promote_follow1",
        "label":       "🇰🇭 100-200 👤 Follow",
        "description": "100-200 Followers 👤\n⏱ 10-20 នាទី",
        "flat_price":  0.99,
    },
    {
        "slug":        "manual_tiktok_promote_follow2",
        "label":       "🇰🇭 300-500 👤 Follow",
        "description": "300-500 Followers 👤\n⏱ 10-20 នាទី",
        "flat_price":  1.99,
    },
]
_changed = False
for _pkg in _TIKTOK_PACKAGES:
    _slug = _pkg["slug"]
    if _slug not in smm_services:
        smm_services[_slug] = {
            "api_id":      None,
            "manual":      True,
            "cost_rate":   0,
            "min":         1,
            "max":         1,
            "label":       _pkg["label"],
            "category":    "🇰🇭 TikTok Khmer",
            "flat_price":  _pkg["flat_price"],
            "preset_qtys": [1],
            "description": _pkg["description"],
        }
        _changed = True
if _changed:
    _save(SMM_SVC_FILE, smm_services)

# Remove old single-package slug if exists
if "manual_tiktok_promote_khmer" in smm_services:
    smm_services.pop("manual_tiktok_promote_khmer")
    _save(SMM_SVC_FILE, smm_services)




waiting      = {}
lang_cooldown= {}

# ═══════════════════════════════════════════════════════════
#  BOT + HTTP
# ═══════════════════════════════════════════════════════════
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ── Premium emoji auto-injection — ជាមួយ AUTO-FALLBACK សុវត្ថិភាព ──────────
# គ្រោះថ្នាក់ដែលត្រូវការពារ៖ បើ custom_emoji_id ណាមួយខូច/លែងមាន ឬ admin
# (ADMIN_ID) លែងមាន Telegram Premium ទៀត Telegram server អាច **បដិសេធ
# request ទាំងមូល** (error) — ដែលនឹងធ្វើឲ្យ send_message/edit_message បរាជ័យ
# ⇒ សារ ឬ button ទាំងមូលនោះនឹង "មិនដំណើរការ" ទាំងស្រុង។
# ដំណោះស្រាយ: ព្យាយាមផ្ញើជាមួយ icon/tg-emoji ជាមុនសិន — បើ Telegram បដិសេធ
# ដោយហេតុផលទាក់ទង emoji/icon/premium ប៉ុណ្ណោះ នោះ retry ដោយ **ដកចេញ** icon
# ទាំងអស់ (fallback ទៅ unicode emoji ធម្មតាវិញ) ដើម្បីធានាថា message/button
# តែងតែផ្ញើចេញបានជោគជ័យ — មិនដែលឲ្យ premium emoji ធ្វើឲ្យ button ខូចឡើយ។
def _emojify(text):
    if not text or not isinstance(text, str) or "<tg-emoji" in text:
        return text
    for ch in _EMOJI_CHARS_SORTED:
        eid = EMOJI_MAP.get(ch)
        if eid and ch in text:
            text = text.replace(ch, f'<tg-emoji emoji-id="{eid}">{ch}</tg-emoji>')
    return text

def _strip_tg_emoji_tags(text):
    """ដកចេញ <tg-emoji ...>x</tg-emoji> ទុកតែ x (unicode emoji ធម្មតា)."""
    if not text or not isinstance(text, str):
        return text
    return _re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', text, flags=_re.DOTALL)

def _strip_markup_icons(markup):
    """ដកចេញ icon_custom_emoji_id ពី button ទាំងអស់ក្នុង keyboard (in place)."""
    if markup is None:
        return markup
    try:
        rows = getattr(markup, "keyboard", None)
        if not rows:
            return markup
        for row in rows:
            for btn in row:
                if hasattr(btn, "_emoji_id"):
                    btn._emoji_id = None
    except Exception:
        pass
    return markup

_EMOJI_ERROR_HINTS = ("EMOJI", "ICON", "PREMIUM", "STICKER")

def _looks_emoji_related(exc):
    return any(h in str(exc).upper() for h in _EMOJI_ERROR_HINTS)

def _wrap_safe_call(fn, text_kw=None, text_pos=None):
    """រុំ bot method មួយ ដើម្បី (1) ដាក់ tg-emoji ចូល text ស្វ័យប្រវត្តិ បើ
    parse_mode=HTML និង (2) ធានាថា បើ Telegram បដិសេធដោយសារ emoji/icon,
    retry ដោយគ្មាន icon វិញ ដើម្បីកុំឲ្យ button/message បរាជ័យ។"""
    def wrapper(*args, **kwargs):
        args = list(args)
        orig_text, emojified = None, False

        if text_kw is not None and kwargs.get("parse_mode") == "HTML":
            if text_kw in kwargs and kwargs[text_kw]:
                orig_text = kwargs[text_kw]
                new_text = _emojify(orig_text)
                if new_text != orig_text:
                    kwargs[text_kw] = new_text
                    emojified = True
            elif text_pos is not None and len(args) > text_pos and isinstance(args[text_pos], str):
                orig_text = args[text_pos]
                new_text = _emojify(orig_text)
                if new_text != orig_text:
                    args[text_pos] = new_text
                    emojified = True

        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if not _looks_emoji_related(e):
                raise
            logger.warning(f"⚠️ Premium emoji ត្រូវបានបដិសេធដោយ Telegram — fallback ទៅ unicode ធម្មតា: {e}")
            if emojified:
                if text_kw is not None and text_kw in kwargs:
                    kwargs[text_kw] = orig_text
                elif text_pos is not None:
                    args[text_pos] = orig_text
            _strip_markup_icons(kwargs.get("reply_markup"))
            return fn(*args, **kwargs)
    return wrapper

bot.send_message        = _wrap_safe_call(bot.send_message,        "text", 1)
bot.reply_to            = _wrap_safe_call(bot.reply_to,             "text", 1)
bot.edit_message_text   = _wrap_safe_call(bot.edit_message_text,    "text", 0)
bot.send_photo          = _wrap_safe_call(bot.send_photo,           "caption", 2)
bot.edit_message_caption= _wrap_safe_call(bot.edit_message_caption, "caption", 0)
bot.edit_message_reply_markup = _wrap_safe_call(bot.edit_message_reply_markup, None, None)

# ═══════════════════════════════════════════════════════════
#  MULTI-BOT  — admin អាចបង្កើត bot ថ្មីពី /newbot ខាងក្នុង Telegram
#  bot ថ្មីដំណើរការជា process ដាច់ដោយឡែក ដោយប្រើ script នេះឯងជា worker
# ═══════════════════════════════════════════════════════════
import subprocess as _subprocess
CLONES_DIR     = _dpath("bot_clones")    # folder ផ្ទុក data របស់ bot រងនីមួយៗ
CLONES_REGISTRY= _dpath("bot_clones.json")
CLONE_BASE_PORT= 5057                   # bot ដើមប្រើ 5056, clone ចាប់ពី 5057
clone_registry = _load(CLONES_REGISTRY, {})   # name -> {token, admin_id, camrapid_key, port, pid}

# ── Sub-admins, Support config, CamRapidPay config (editable at runtime) ──
sub_admins   = _load(SUB_ADMIN_FILE,   [])          # list of int UIDs
support_cfg  = _load(SUPPORT_CFG_FILE, {"kh": "", "en": ""})   # custom support text per lang
camrapid_cfg = _load(CAMRAPID_CFG_FILE, {"key": ""})            # live-editable API key

def _effective_camrapid_key():
    """Return runtime key if set, else fall back to env/default"""
    return camrapid_cfg.get("key") or CAMRAPID_API_KEY

def is_admin(uid):
    """True if uid is master admin OR sub-admin"""
    return uid == ADMIN_ID or uid in sub_admins
clone_procs    = {}                            # name -> subprocess.Popen (តែក្នុង process នេះប៉ុណ្ណោះ)

def _clone_dir(name):
    d = os.path.join(CLONES_DIR, name)
    os.makedirs(d, exist_ok=True)
    return d

def _next_clone_port():
    used = {v.get("port") for v in clone_registry.values()}
    p = CLONE_BASE_PORT
    while p in used:
        p += 1
    return p

def _clone_is_running(name):
    proc = clone_procs.get(name)
    return proc is not None and proc.poll() is None

def _spawn_clone(name, cfg):
    env = os.environ.copy()
    env["BOT_TOKEN"]        = cfg["token"]
    env["ADMIN_ID"]         = str(cfg["admin_id"])
    env["CAMRAPID_API_KEY"] = cfg["camrapid_key"]
    env["CONTROL_PORT"]     = str(cfg["port"])
    env["CONTROL_KEY"]      = f"ctrl_{name}"
    env["INSTANCE_NAME"]    = name
    env["BOT_DISPLAY_NAME"] = cfg.get("display_name", name)
    env["BOT_WELCOME_MSG"]  = cfg.get("welcome_msg", "")
    wdir = _clone_dir(name)
    logf = open(os.path.join(wdir, "bot.log"), "a", encoding="utf-8")
    proc = _subprocess.Popen(
        [sys.executable, os.path.abspath(__file__)],
        cwd=wdir, env=env, stdout=logf, stderr=_subprocess.STDOUT,
    )
    clone_procs[name] = proc
    return proc

def _stop_clone(name):
    proc = clone_procs.get(name)
    if proc and proc.poll() is None:
        proc.terminate()
        try: proc.wait(timeout=8)
        except _subprocess.TimeoutExpired: proc.kill()
    clone_procs.pop(name, None)

def _clone_watchdog():
    while True:
        time.sleep(20)
        for name, cfg in list(clone_registry.items()):
            if not _clone_is_running(name):
                logger.warning(f"Clone '{name}' not running — starting/restarting...")
                try:
                    _spawn_clone(name, cfg)
                    bot.send_message(ADMIN_ID, f"⚠️ Bot '{name}' ត្រូវបាន (re)start ស្វ័យប្រវត្តិ។")
                except Exception as e:
                    logger.error(f"Clone watchdog failed for {name}: {e}")


def _make_session():
    s = http_req.Session()
    r = Retry(total=3, backoff_factor=2, status_forcelist=[500,502,503,504])
    a = HTTPAdapter(max_retries=r)
    s.mount("http://", a); s.mount("https://", a)
    return s
http = _make_session()

# ═══════════════════════════════════════════════════════════
#  LANGUAGE
# ═══════════════════════════════════════════════════════════
STRINGS = {
    "kh": {
        "welcome": (
            "សួស្តី បង/ប្អូន! 👋\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "ស្វាគមន៍មក <b>Kaijaklike</b> 🇰🇭\n"
            "ខ្ញុំជួយបង្កើន Views · Likes · Followers\n"
            "សម្រាប់ TikTok និង Social Media ផ្សេងៗ!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💳 លុយបច្ចុប្បន្ន: <b>${:.2f}</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "👇 ចុចជ្រើសពី Menu ខាងក្រោមបាន!"
        ),
        "select_lang":   "🌐 ជ្រើសភាសាដែលអ្នកចូលចិត្ត:",
        "lang_set":      "✅ ផ្លាស់ប្តូរភាសារួចហើយ!",
        "menu":          "🏠 ត្រឡប់ Menu",
        "banned":        "🚫 គណនីរបស់អ្នកត្រូវបាន ban! សូមទំនាក់ Admin ប្រសិនបើមានបញ្ហា។",
        "cancel_ok":     "🏠 ត្រឡប់ Menu ហើយ! 😊",
        "no_service":    "❌ មិនទាន់មាន Service ទេ នឹងដាក់ឆាប់ៗ!",
        "choose_platform": "ជ្រើស Platform ដែលចង់ boost:",
        "choose_qty":    "ជ្រើស Package:",
        "send_link":     "ផ្ញើ Link វីដេអូរបស់អ្នកមក:",
        "low_balance":   "❌ លុយមិនគ្រប់! សូម Top Up ជាមុន 💸",
        "order_done":    "✅ Order បានទទួលហើយ! នឹងដំណើរការឆាប់ៗ 🙏\nអរគុណដែលប្រើសេវា Kaijaklike! 💙",
        "deposit_ok":    "✅ ដាក់លុយបានជោគជ័យ! 🎉\nអរគុណច្រើនដែលបន្ថែម Balance! 💙 Kaijaklike",
        "qr_expired":    "⏰ QR ផុតហើយ! សូម Top Up ម្តងទៀតនៅ",
        "qr_error":      "⚠️ មានបញ្ហា Generate QR! សូមទំនាក់ Admin 🙏",
        "track_prompt":  "🔍 វាយ Order ID របស់អ្នក (ឧ: KZ12345):",
        "order_notfound":"❌ រកមិនឃើញ Order នេះទេ! ត្រូវប្រាកដ ID ត្រឹមត្រូវ",
        "no_orders":     "❌ មិនទាន់មាន Order ណាមួយទេ!",
        "how_to_use": (
            "💡 <b>របៀបប្រើ Kaijaklike</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ ដាក់លុយ → ចុច <b>💸 បញ្ចូលលុយ</b> → Scan QR\n"
            "2️⃣ Order → ចុច <b>🛒 បញ្ជាទិញ</b> → ជ្រើស Package → ផ្ញើ Link\n"
            "3️⃣ តាមដាន → ចុច <b>📋 ប្រវត្តិ</b> → មើលស្ថានភាព Order\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "❓ មានសំណួរ ទំនាក់ Admin បានគ្រប់ពេល! 😊"
        ),
        "support_msg": (
            "💬 <b>ទំនាក់ Admin Kaijaklike</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📞 Admin: @smos_sne1\n"
            "⏱ ទំនាក់បានគ្រប់ពេល!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💡 មានបញ្ហា Order ឬ Payment\n"
            "ផ្ញើ Order ID មកផ្ទាល់ Admin 🙏"
        ),
        "fallback": "😊 ប្រើប៊ូតុង Menu ខាងក្រោមបាន!",
    },
    "en": {
        "welcome": (
            "Hey! 👋 Welcome to <b>Kaijaklike</b> 🇰🇭\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "We help grow your TikTok & Social Media\n"
            "Views · Likes · Followers — fast & real!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💳 Your Balance: <b>${:.2f}</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "👇 Pick from the menu below!"
        ),
        "select_lang":   "🌐 Choose your language:",
        "lang_set":      "✅ Language updated!",
        "menu":          "🏠 Back to Menu",
        "banned":        "🚫 Your account has been banned. Contact Admin if you think this is a mistake.",
        "cancel_ok":     "🏠 Back to Menu!",
        "no_service":    "❌ No services yet — check back soon!",
        "choose_platform": "Pick a platform to boost:",
        "choose_qty":    "Choose a package:",
        "send_link":     "Send your video link:",
        "low_balance":   "❌ Not enough balance! Please Top Up first 💸",
        "order_done":    "✅ Order received! We'll process it shortly 🙏\nThank you for using Kaijaklike! 💙",
        "deposit_ok":    "✅ Deposit successful! 🎉\nThank you for topping up! 💙 Kaijaklike",
        "qr_expired":    "⏰ QR expired! Please Top Up again",
        "qr_error":      "⚠️ QR error! Please contact Admin 🙏",
        "track_prompt":  "🔍 Send your Order ID (e.g. KZ12345):",
        "order_notfound":"❌ Order not found! Make sure the ID is correct.",
        "no_orders":     "❌ No orders yet!",
        "how_to_use": (
            "💡 <b>How to use Kaijaklike</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ Top Up → Tap <b>💸 Top Up</b> → Scan QR\n"
            "2️⃣ Order → Tap <b>🛒 Order</b> → Pick package → Send link\n"
            "3️⃣ Track → Tap <b>📋 History</b> → Check status\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "❓ Questions? Contact Admin anytime! 😊"
        ),
        "support_msg": (
            "💬 <b>Contact Kaijaklike Admin</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📞 Admin: @smos_sne1\n"
            "⏱ Available anytime!\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "💡 For order or payment issues,\n"
            "send your Order ID directly to Admin 🙏"
        ),
        "fallback": "😊 Use the menu buttons below!",
    },
}

def get_lang(uid): return user_lang.get(str(uid), "kh")

def t(uid, key, *args):
    lang = get_lang(uid)
    s = STRINGS.get(lang, STRINGS["kh"]).get(key) or STRINGS["kh"].get(key, key)
    if args:
        try: return s.format(*args)
        except: return s
    return s

def lang_select_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇰🇭 ខ្មែរ", callback_data="setlang:kh", color="active"),
         InlineKeyboardButton("🇬🇧 English", callback_data="setlang:en", color="active")]
    ])

# ═══════════════════════════════════════════════════════════
#  WALLET HELPERS
# ═══════════════════════════════════════════════════════════
def bal(uid): return float(wallets.get(str(uid), 0))
def add_bal(uid, amt):
    wallets[str(uid)] = round(bal(uid) + amt, 2)
    _save(WALLETS_FILE, wallets)
def ded_bal(uid, amt):
    wallets[str(uid)] = max(0, round(bal(uid) - amt, 2))
    _save(WALLETS_FILE, wallets)
def set_bal(uid, amt):
    wallets[str(uid)] = round(float(amt), 2)
    _save(WALLETS_FILE, wallets)

# ═══════════════════════════════════════════════════════════
#  PROMO CODE
# ═══════════════════════════════════════════════════════════
def apply_promo(uid, code, amount):
    code = code.strip().upper()
    p = promos.get(code)
    if not p: return amount, 0, "❌ Promo Code ខុស!"
    if p.get("uses", 0) > 0 and p.get("used", 0) >= p["uses"]:
        return amount, 0, "❌ Promo Code ផុតសិទ្ធហើយ!"
    user_used = p.get("user_used", {})
    if str(uid) in user_used:
        return amount, 0, "❌ អ្នកបានប្រើ Promo Code នេះហើយ!"
    if p.get("pct", False):
        discount = round(amount * float(p["discount"]) / 100, 2)
    else:
        discount = min(float(p["discount"]), amount)
    final = max(0, round(amount - discount, 2))
    return final, discount, None

def confirm_promo(code, uid):
    code = code.strip().upper()
    p = promos.get(code)
    if not p: return
    p["used"] = p.get("used", 0) + 1
    uu = p.get("user_used", {})
    uu[str(uid)] = 1
    p["user_used"] = uu
    _save(PROMO_FILE, promos)

# ═══════════════════════════════════════════════════════════
#  SMM HELPERS
# ═══════════════════════════════════════════════════════════
def _smm_get_categories():
    cats = []
    for s in smm_services.values():
        c = s.get("category", "Other")
        if c not in cats: cats.append(c)
    return cats

def _smm_get_svcs_in_cat(cat):
    return [(slug, s) for slug, s in smm_services.items() if s.get("category") == cat]

def _auto_dep_bonus(amount):
    """ត្រឡប់ Bonus ស្វ័យប្រវត្តិ (USD) សម្រាប់ចំនួនប្រាក់ដែលដាក់ — 0 បើមិនចូលលក្ខខណ្ឌ។"""
    try:
        if not dep_bonus_cfg.get("enabled", True):
            return 0.0
        amount = float(amount)
        min_amt = float(dep_bonus_cfg.get("min_amount", 1.0))
        if amount < min_amt:
            return 0.0
        pct = float(dep_bonus_cfg.get("pct", 5.0))
        if pct <= 0:
            return 0.0
        return round(amount * pct / 100, 2)
    except Exception:
        return 0.0

def _dep_bonus_status_text():
    c = dep_bonus_cfg
    if not c.get("enabled", True):
        return "🎁 <b>Bonus ដាក់លុយ៖</b> <i>បិទ</i>"
    return (f"🎁 <b>Bonus ដាក់លុយ៖</b> <b>{float(c.get('pct',5.0)):.0f}%</b> "
            f"(ដាក់ចាប់ពី <b>${float(c.get('min_amount',1.0)):.2f}</b> ឡើងទៅ)")

def _smm_profit_pct(): return float(smm_profit.get("pct", 20))

def _smm_sell_rate(cost, slug=None):
    s = smm_services.get(slug, {})
    if s.get("flat_price"): return float(s["flat_price"]) * 1000  # convert to per-1K for display
    if s.get("custom_price"): return float(s["custom_price"])
    return round(float(cost) * (1 + _smm_profit_pct() / 100), 4)

def _smm_price_for_order(slug, qty):
    """Get actual price for an order (handles flat_price services)"""
    s = smm_services.get(slug, {})
    if s.get("flat_price"):
        return float(s["flat_price"])  # flat: always $0.99 regardless of qty
    sr = _smm_sell_rate(s.get("cost_rate", 0), slug)
    return round(sr * qty / 1000, 4)

def _smm_api_post(params, timeout=25):
    url = smm_api.get("url", "")
    if not url: return None
    try:
        r = http.post(url, data=params, timeout=timeout)
        return r.json()
    except Exception as e:
        logger.error(f"SMM API: {e}"); return None

def _smm_fetch_service(api_id):
    key = smm_api.get("key", "")
    url = smm_api.get("url", "")
    if not key or not url:
        logger.error("SMM API: url or key not set")
        return None
    try:
        r = http.post(url, data={"key": key, "action": "services"}, timeout=30)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and data.get("error"):
            logger.error(f"SMM API error: {data['error']}")
            return None
        for s in data:
            if str(s.get("service")) == str(api_id):
                # API panels use "rate" as cost per 1000, some use "min" fallback
                rate = s.get("rate") or s.get("price") or s.get("cost") or "0"
                return {
                    "cost_rate": str(rate),
                    "min":       max(1, int(float(s.get("min") or 10))),
                    "max":       int(float(s.get("max") or 100000)),
                    "raw_name":  s.get("name") or s.get("Name") or str(api_id),
                }
        logger.error(f"SMM API: service {api_id} not found in list")
    except Exception as e:
        logger.error(f"Fetch service {api_id}: {e}")
    return None

def _smm_clean_name(raw):
    raw = re.sub(r'\s*\[.*?\]\s*', ' ', raw)
    raw = re.sub(r'\s*\(.*?\)\s*', ' ', raw)
    return re.sub(r'\s+', ' ', raw).strip()[:60]

def _smm_service_list_text():
    if not smm_services: return "❌ គ្មាន Service ទេ"
    lines = ["<b>📋 SMM Services</b>\n━━━━━━━━━━━━━━━━━━"]
    for cat in _smm_get_categories():
        lines.append(f"\n📂 <b>{cat}</b>")
        for slug, s in _smm_get_svcs_in_cat(cat):
            sr = _smm_sell_rate(s["cost_rate"], slug)
            lines.append(f"  • {s.get('label',slug)} — ${sr:.2f}/1K")
    return "\n".join(lines)

# ── Hardcoded notify channel — always works ──
NOTIFY_CHANNEL_ID_DEFAULT = -1003930705105

def _notify(msg):
    """Send message to notify channel — always use hardcoded ID"""
    cid = NOTIFY_CHANNEL_ID_DEFAULT
    # Override with file/env if admin changed it
    try:
        cfg = _load(NOTIFY_FILE, {})
        saved_cid = cfg.get("channel_id", "")
        if saved_cid:
            cid = int(saved_cid)
    except:
        pass
    try:
        bot.send_message(cid, msg, parse_mode="HTML")
        logger.info(f"[notify] sent to {cid}")
    except Exception as e:
        logger.warning(f"[notify] failed cid={cid} err={e}")

def _send_order_notify(uid, oid, label, qty, link, price):
    _notify(
        f"🛒 <b>Order ថ្មី!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 User ID: <code>{uid}</code>\n"
        f"📦 សេវា: {label}\n"
        f"🔢 ចំនួន: {qty:,}\n"
        f"💵 តម្លៃ: <b>${price:.2f}</b>\n"
        f"🆔 Order ID: <code>{oid}</code>\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

def _send_deposit_notify(uid, amount, bonus, new_bal):
    msg = (
        f"💰 <b>ដាក់លុយ ថ្មី!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 User ID: <code>{uid}</code>\n"
        f"💵 បានទទួល: <b>${amount:.2f}</b>\n"
    )
    if bonus > 0:
        msg += f"🎟️ Bonus: <b>+${bonus:.2f}</b>\n"
    msg += (
        f"💳 Balance ថ្មី: <b>${new_bal:.2f}</b>\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    _notify(msg)

def _get_notify_cfg():
    cfg = _load(NOTIFY_FILE, {})
    if not cfg.get("channel_id"):
        cfg = {"channel_id": str(NOTIFY_CHANNEL_ID_DEFAULT), "enabled": True}
    cfg["enabled"] = True
    return cfg

def _make_order_id():
    return f"KZ{int(time.time())%100000:05d}"

def _place_smm_order(uid, slug, qty, link):
    uid_str = str(uid)
    s = smm_services.get(slug)
    if not s: return None, "❌ Service រកមិនឃើញ"
    sr    = _smm_sell_rate(s["cost_rate"], slug)
    price = sr * qty / 1000
    if bal(uid) < price: return None, f"❌ Balance មិនគ្រប់! (Balance: ${bal(uid):.2f})"
    ded_bal(uid, price)
    key = smm_api.get("key",""); url = smm_api.get("url","")
    res = None
    if key and url:
        res = _smm_api_post({"key": key, "action": "add",
                             "service": s["api_id"], "link": link, "quantity": qty})
    api_order_id = str(res.get("order","")) if res else ""
    oid = _make_order_id()
    smm_orders[oid] = {
        "uid": uid_str, "slug": slug, "label": s.get("label",slug),
        "qty": qty, "price": price, "link": link, "api_order_id": api_order_id,
        "status": "pending", "ts": int(time.time()),
    }
    _save(SMM_ORD_FILE, smm_orders)
    # Notify channel directly — no config dependency
    try:
        ord_msg = (
            f"🛒 <b>Order ថ្មី!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 User ID: <code>{uid}</code>\n"
            f"📦 សេវា: {s.get('label', slug)}\n"
            f"🔢 ចំនួន: {qty:,}\n"
            f"💵 តម្លៃ: <b>${price:.2f}</b>\n"
            f"🆔 Order ID: <code>{oid}</code>\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(NOTIFY_CHANNEL_ID_DEFAULT, ord_msg, parse_mode="HTML")
        logger.info(f"[order_notify] sent uid={uid} oid={oid}")
    except Exception as e:
        logger.warning(f"[order_notify] failed: {e}")
    return oid, None

# ═══════════════════════════════════════════════════════════
#  KHQR CARD GENERATOR  (Bakong-style branded card)
# ═══════════════════════════════════════════════════════════
_CARD_NAVY      = (13, 18, 38)
_CARD_NAVY2     = (30, 27, 75)
_CARD_RED       = (229, 29, 39)
_CARD_WHITE     = (255, 255, 255)
_CARD_SUBTITLE  = (191, 196, 234)
_CARD_GRAY      = (104, 110, 128)
_CARD_MUTED     = (139, 140, 144)
_CARD_BORDER    = (228, 229, 233)
_CARD_GOLD      = (245, 197, 66)
_CARD_VIOLET    = (124, 92, 255)
_CARD_PANEL     = (250, 250, 252)

_FONT_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/system/fonts/Roboto-Regular.ttf",
    "/data/data/com.termux/files/usr/share/fonts/DejaVuSans.ttf",
]
_FONT_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/system/fonts/Roboto-Bold.ttf",
    "/data/data/com.termux/files/usr/share/fonts/DejaVuSans-Bold.ttf",
]

def _card_font(size, bold=False):
    for path in (_FONT_BOLD if bold else _FONT_REG):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default(size=size)

def _tw(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)[2]

def _cx_text(draw, cx, y, text, font, fill):
    draw.text((cx - _tw(draw, text, font) / 2, y), text, font=font, fill=fill)

def _vgrad(draw, box, top_color, bottom_color):
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    for i in range(h):
        t = i / h
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        draw.line([(x0, y0 + i), (x1, y0 + i)], fill=(r, g, b))

def _qr_matrix(data):
    try:
        import qrcode as _qrcode
        qr = _qrcode.QRCode(border=0, error_correction=_qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(data); qr.make(fit=True)
        m = qr.get_matrix()
        return np.array([[0 if c else 255 for c in row] for row in m], dtype=np.uint8)
    except Exception as e:
        raise RuntimeError(f"qrcode lib error: {e}")

def _qr_img(data, box_px):
    matrix = _qr_matrix(data)
    n = matrix.shape[0]
    mod = max(1, box_px // n)
    img = Image.new("RGB", (mod * n, mod * n), _CARD_PANEL)
    draw = ImageDraw.Draw(img)
    for ry in range(n):
        for rx in range(n):
            if matrix[ry, rx] == 0:
                x0, y0 = rx * mod, ry * mod
                draw.rectangle([x0, y0, x0 + mod - 1, y0 + mod - 1], fill=_CARD_NAVY)
    return img.resize((box_px, box_px), Image.LANCZOS)

def _build_qr_image(qr_string, amount=None, ref=None, label=None, subtitle=None,
                    expires_min=None, width=720):
    """Generate branded KHQR card → BytesIO (PNG). Falls back to plain QR on error."""
    if expires_min is None:
        expires_min = max(1, round(DEPOSIT_EXPIRE_SEC / 60))
    try:
        W = width
        HEADER_H = int(W * 0.30)
        SIDE_PAD = int(W * 0.13)
        QR_BOX   = W - 2 * SIDE_PAD
        QR_PAD   = int(QR_BOX * 0.09)
        OVERLAP  = int(W * 0.10)

        f_title = _card_font(int(W * 0.052), bold=True)
        f_sub   = _card_font(int(W * 0.026))
        f_name  = _card_font(int(W * 0.042), bold=True)
        f_label = _card_font(int(W * 0.024))
        f_amt   = _card_font(int(W * 0.062), bold=True)
        f_small = _card_font(int(W * 0.0205))
        f_badge = _card_font(int(W * 0.0195), bold=True)

        qr_card_top    = HEADER_H - OVERLAP
        qr_card_bottom = qr_card_top + QR_BOX
        content_top    = qr_card_bottom + int(W * 0.05)

        amt_h = int(f_amt.size * 1.5)
        gap1, gap2 = int(W * 0.022), int(W * 0.035)
        bottom_pad = int(W * 0.05)

        H = (content_top
             + int(W * 0.065)
             + int(W * 0.04)
             + gap1 + amt_h + gap2
             + int(W * 0.03) * 4
             + bottom_pad)

        img  = Image.new("RGB", (W, H), _CARD_WHITE)
        draw = ImageDraw.Draw(img)
        cx   = W // 2
        pad  = int(W * 0.06)

        # 1. Gradient header
        _vgrad(draw, [0, 0, W, HEADER_H], _CARD_NAVY, _CARD_NAVY2)

        # Decorative ring
        ring_r = int(W * 0.32)
        ring_cx, ring_cy = W - int(W * 0.05), int(W * 0.02)
        draw.ellipse([ring_cx - ring_r, ring_cy - ring_r, ring_cx + ring_r, ring_cy + ring_r],
                     outline=(255, 255, 255), width=1)

        draw.text((pad, int(W * 0.045)), "KHQR", font=f_title, fill=_CARD_WHITE)
        draw.text((pad, int(W * 0.045) + f_title.size + int(W * 0.010)),
                  "Cambodian QR Payment · Bakong", font=f_sub, fill=_CARD_SUBTITLE)

        # Gold badge
        badge_txt = "★ PREMIUM"
        bw = _tw(draw, badge_txt, f_badge)
        bpad_x, bpad_y = int(W * 0.020), int(W * 0.011)
        bx1 = W - pad
        bx0 = bx1 - bw - bpad_x * 2
        by0 = int(W * 0.045)
        by1 = by0 + f_badge.size + bpad_y * 2
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=(by1 - by0) // 2, fill=_CARD_GOLD)
        draw.text((bx0 + bpad_x, by0 + bpad_y - int(W * 0.003)), badge_txt, font=f_badge, fill=_CARD_NAVY)

        # 2. Floating QR panel
        r = int(W * 0.045)
        panel_box = [SIDE_PAD, qr_card_top, SIDE_PAD + QR_BOX, qr_card_bottom]
        shadow_off = int(W * 0.012)
        draw.rounded_rectangle(
            [panel_box[0] + shadow_off, panel_box[1] + shadow_off,
             panel_box[2] + shadow_off, panel_box[3] + shadow_off],
            radius=r, fill=(225, 227, 235))
        draw.rounded_rectangle(panel_box, radius=r, fill=_CARD_WHITE)

        qr_px  = QR_BOX - 2 * QR_PAD
        qr_pil = _qr_img(qr_string, qr_px)
        img.paste(qr_pil, (SIDE_PAD + QR_PAD, qr_card_top + QR_PAD))

        # Violet corner brackets
        bl = int(W * 0.055)
        bt = max(3, int(W * 0.007))
        bo = int(W * 0.018)
        x0, y0, x1, y1 = panel_box
        corners = [
            ((x0+bo, y0+bo+bl), (x0+bo, y0+bo), (x0+bo+bl, y0+bo)),
            ((x1-bo-bl, y0+bo), (x1-bo, y0+bo), (x1-bo, y0+bo+bl)),
            ((x0+bo, y1-bo-bl), (x0+bo, y1-bo), (x0+bo+bl, y1-bo)),
            ((x1-bo-bl, y1-bo), (x1-bo, y1-bo), (x1-bo, y1-bo-bl)),
        ]
        for pts in corners:
            draw.line(pts, fill=_CARD_VIOLET, width=bt, joint="curve")

        # 3. Store name + subtitle
        y = content_top
        _cx_text(draw, cx, y, label or "Kaijaklike", f_name, _CARD_NAVY)
        y += int(W * 0.065)
        _cx_text(draw, cx, y, subtitle or "SMM Panel Deposit", f_label, _CARD_GRAY)
        y += int(W * 0.04) + gap1

        # 4. Amount banner
        if amount is not None:
            amt_str = f"${float(amount):.2f}"
            banner_box = [pad, y, W - pad, y + amt_h]
            draw.rounded_rectangle(banner_box, radius=int(W * 0.02), fill=(243, 241, 255))
            draw.rounded_rectangle(banner_box, radius=int(W * 0.02), outline=_CARD_VIOLET, width=2)
            _cx_text(draw, cx, y + (amt_h - f_amt.size) // 2 - int(W * 0.010),
                     amt_str, f_amt, _CARD_NAVY2)
            y += amt_h + gap2

        # 5. Ref / expiry / footer
        if ref:
            _cx_text(draw, cx, y, f"Ref: {ref}", f_small, _CARD_MUTED)
            y += int(W * 0.03)
        if expires_min:
            _cx_text(draw, cx, y, f"Expires in {expires_min} minutes", f_small, _CARD_RED)
            y += int(W * 0.03)
        _cx_text(draw, cx, y, "Scan with any Bakong-member app", f_small, _CARD_MUTED)
        y += int(W * 0.03)
        _cx_text(draw, cx, y, "ABA · ACLEDA · Wing", f_small, _CARD_MUTED)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0); buf.name = "khqr_card.png"
        return buf

    except Exception as e:
        logger.warning(f"[build_qr_image] {e}")
        try:
            import qrcode as _qrc
            qr = _qrc.QRCode(box_size=8, border=2,
                             error_correction=_qrc.constants.ERROR_CORRECT_M)
            qr.add_data(qr_string); qr.make(fit=True)
            pil = qr.make_image(fill_color=(10, 34, 64), back_color="white").convert("RGB")
            buf = io.BytesIO(); pil.save(buf, format="PNG")
            buf.seek(0); buf.name = "khqr.png"
            return buf
        except:
            return None

# ═══════════════════════════════════════════════════════════
#  CAMRAPIDPAY — Create KHQR + Check payment
#  (v9: replace manual EMV TLV with CamRapidPay API)
# ═══════════════════════════════════════════════════════════

def _camrapid_create(uid, amount, reference):
    """Create KHQR payment via CamRapidPay API — returns response dict or None"""
    payload = {
        "api_key":   _effective_camrapid_key(),
        "amount":    round(float(amount), 2),
        "reference": reference,
    }
    if WEBHOOK_URL:
        payload["webhook_url"] = WEBHOOK_URL
    else:
        payload["webhook_url"] = f"https://placeholder.kairozen.store/wh/{reference}"

    logger.info(f"[camrapid_create] uid={uid} ref={reference} amount={payload['amount']}")
    try:
        r = http.post(CAMRAPID_CREATE,
                      json=payload,
                      headers={"Content-Type": "application/json",
                               "Accept": "application/json"},
                      timeout=15)
        logger.info(f"[camrapid_create] HTTP {r.status_code}")
        data = r.json()
        logger.info(f"[camrapid_create] resp={data}")
        if data.get("success"):
            return data   # keys: qr_code, payment_url, bill_number, amount, expires_in
        logger.error(f"[camrapid_create] failed: {data}")
        return None
    except Exception as e:
        logger.error(f"[camrapid_create] exception: {e}")
        return None

def _camrapid_check(reference) -> bool:
    """Check payment status via CamRapidPay API — returns True if paid"""
    try:
        r = http.get(
            CAMRAPID_CHECK,
            params={"api_key": _effective_camrapid_key(), "reference": reference},
            headers={"Accept": "application/json"},
            timeout=10,
        )
        data = r.json()
        logger.info(f"[camrapid_check] ref={reference} resp={data}")
        return data.get("success") and data.get("status") in ("Success", "success", "PAID", "paid")
    except Exception as e:
        logger.error(f"[camrapid_check] {e}")
        return False

def _watch_deposit(uid, uid_str, dep_id, amount, reference):
    """Poll CamRapidPay until paid or expired (5 min)"""
    deadline = time.time() + DEPOSIT_EXPIRE_SEC + 30
    while time.time() < deadline:
        dep = smm_deps.get(dep_id)
        if not dep or dep.get("status") != "pending": return
        if _camrapid_check(reference):
            bonus       = float(dep.get("bonus") or 0)
            promo_bonus = float(dep.get("promo_bonus") or 0)
            auto_bonus  = float(dep.get("auto_bonus") or 0)
            total = round(amount + bonus, 2)
            add_bal(uid, total)
            smm_deps[dep_id]["status"] = "confirmed"
            _save(SMM_DEP_FILE, smm_deps)
            new_b = bal(uid)
            msg = (f"✅ <b>ដាក់លុយបានជោគជ័យហើយ!</b> 🎉\n"
                   f"━━━━━━━━━━━━━━━━━━\n"
                   f"💰 បានទទួល: <b>${amount:.2f}</b>")
            if promo_bonus > 0:
                msg += f"\n🎟️ Promo Bonus: <b>+${promo_bonus:.2f}</b>"
            if auto_bonus > 0:
                msg += f"\n🎁 Auto Bonus: <b>+${auto_bonus:.2f}</b>"
            msg += f"\n💳 Balance: <b>${new_b:.2f}</b>\n━━━━━━━━━━━━━━━━━━\n💙 អរគុណដែលប្រើ Kaijaklike!"
            try: bot.send_message(uid, msg, parse_mode="HTML", reply_markup=main_kb(uid))
            except: pass
            try:
                bot.send_message(ADMIN_ID,
                    f"💰 <b>ដាក់លុយ ✅</b>\n👤 <code>{uid_str}</code>\n"
                    f"📌 Ref: <code>{reference}</code>\n"
                    f"💰 ${amount:.2f}" + (f" + Bonus ${bonus:.2f}" if bonus > 0 else "") +
                    (f" (Promo ${promo_bonus:.2f} / Auto ${auto_bonus:.2f})" if (promo_bonus > 0 and auto_bonus > 0) else ""),
                    parse_mode="HTML")
            except: pass
            # Notify channel — call _notify directly to avoid any config issues
            try:
                dep_msg = (
                    f"💰 <b>ដាក់លុយ ថ្មី!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 User ID: <code>{uid}</code>\n"
                    f"💵 បានទទួល: <b>${amount:.2f}</b>\n"
                )
                if bonus > 0:
                    dep_msg += f"🎟️ Bonus: <b>+${bonus:.2f}</b>\n"
                dep_msg += f"💳 Balance ថ្មី: <b>${new_b:.2f}</b>\n━━━━━━━━━━━━━━━━━━"
                bot.send_message(NOTIFY_CHANNEL_ID_DEFAULT, dep_msg, parse_mode="HTML")
                logger.info(f"[deposit_notify] sent uid={uid} amount={amount}")
            except Exception as e:
                logger.warning(f"[deposit_notify] failed: {e}")
            return
        time.sleep(POLL_INTERVAL)
    dep = smm_deps.get(dep_id)
    if dep and dep.get("status") == "pending":
        dep["status"] = "expired"; _save(SMM_DEP_FILE, smm_deps)
        try: bot.send_message(uid, "⏰ <b>QR ផុតកំណត់!</b> សូម top up ម្តងទៀត", parse_mode="HTML")
        except: pass

def _send_deposit_qr(uid, amount, promo_code=None, label="💸 ដាក់លុយ", bonus=0.0, promo_code_name=None,
                      promo_bonus=0.0, auto_bonus=0.0):
    """Create KHQR via CamRapidPay API → send branded QR card to user"""
    uid_str       = str(uid)
    promo_applied = promo_code_name
    reference     = f"KZ{uid}_{int(time.time())}"[:50]

    # Call CamRapidPay API to create KHQR
    resp = _camrapid_create(uid, amount, reference)
    if not resp:
        bot.send_message(uid, "⚠️ <b>មានបញ្ហា Generate QR!</b>\nសូមព្យាយាមម្តងទៀត ឬ ទំនាក់ Admin",
                         parse_mode="HTML")
        return

    qr_str      = resp.get("qr_code", "")
    payment_url = resp.get("payment_url", "")

    dep_id = f"dep_{uid}_{int(time.time())}"
    smm_deps[dep_id] = {
        "uid":         uid_str,
        "amount":      amount,
        "status":      "pending",
        "bonus":       bonus,
        "promo_bonus": promo_bonus,
        "auto_bonus":  auto_bonus,
        "promo":       promo_applied or "",
        "reference":   reference,
        "payment_url": payment_url,
    }
    _save(SMM_DEP_FILE, smm_deps)

    if promo_applied and promo_bonus > 0:
        confirm_promo(promo_applied, uid)

    # Caption text (shown below card photo)
    ref_short = reference[-12:] if len(reference) > 12 else reference
    bonus_bits = []
    if promo_bonus > 0:
        bonus_bits.append(f"🎟️ Promo Bonus: <b>+${promo_bonus:.2f}</b> ({promo_applied})")
    if auto_bonus > 0:
        bonus_bits.append(f"🎁 Auto Bonus ({dep_bonus_cfg.get('pct',5):.0f}%): <b>+${auto_bonus:.2f}</b>")
    bonus_line = ("\n" + "\n".join(bonus_bits)) if bonus_bits else ""
    cap = (f"💸 <b>SMM Panel — បញ្ចូលលុយ</b>{bonus_line}\n"
           f"💰 Amount: <b>${amount:.2f}</b>\n"
           f"🔖 Ref: <code>{ref_short}</code>\n"
           f"⏱ Expires in: <b>5 minutes</b>\n"
           f"✅ <i>ប្រព័ន្ធ auto-detect — Balance update ភ្លាមៗ!</i>")

    # Generate branded KHQR card
    img_buf = None
    if qr_str:
        img_buf = _build_qr_image(
            qr_str,
            amount=amount,
            ref=ref_short,
            label="SMM TOPUP",
            subtitle="SMM Panel Deposit · ដាក់លុយ",
        )

    if img_buf:
        try:
            bot.send_photo(uid, img_buf, caption=cap, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"[deposit_qr] send_photo failed: {e}")
            bot.send_message(uid, cap, parse_mode="HTML")
    else:
        bot.send_message(uid, cap, parse_mode="HTML")

    threading.Thread(target=_watch_deposit,
                     args=(uid, uid_str, dep_id, amount, reference), daemon=True).start()

def _get_dep_promo(uid):
    step = waiting.get(uid)
    if isinstance(step, dict):
        return step.get("promo")
    return None

def _process_deposit(uid, uid_str, amount, promo_code=None):
    lang  = get_lang(uid)
    promo_bonus = 0.0
    promo_applied = None
    if promo_code:
        p = promos.get(promo_code.upper())
        if p and (p.get("uses", 0) == 0 or p.get("used", 0) < p.get("uses", 0)):
            if str(uid) not in p.get("user_used", {}):
                if p.get("pct", False):
                    promo_bonus = round(amount * float(p["discount"]) / 100, 2)
                else:
                    promo_bonus = round(float(p["discount"]), 2)
                promo_applied = promo_code.upper()
    # ── Auto Deposit Bonus (stacks on top of any promo bonus) ──
    auto_bonus  = _auto_dep_bonus(amount)
    total_bonus = round(promo_bonus + auto_bonus, 2)
    _send_deposit_qr(uid, amount,
                     label=f"💸 <b>{'ដាក់លុយ' if lang=='kh' else 'Top Up'}</b>",
                     bonus=total_bonus, promo_code_name=promo_applied,
                     promo_bonus=promo_bonus, auto_bonus=auto_bonus)

# ═══════════════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════════════
def main_kb(uid=None):
    lang = get_lang(uid) if uid else "kh"
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    e = EMOJI_MAP
    if lang == "en":
        kb.row(KeyboardButton("👤 My Account", emoji_id=e.get("account"), color="active"),
               KeyboardButton("💸 Top Up",      emoji_id=e.get("topup"),   color="progress"))
        kb.row(KeyboardButton("🛒 Order Service", emoji_id=e.get("order"), color="active"))
        kb.row(KeyboardButton("📋 Order History", emoji_id=e.get("history"), color="active"),
               KeyboardButton("🔍 Track Order",   emoji_id=e.get("track"),   color="active"))
        kb.row(KeyboardButton("💬 Support", emoji_id=e.get("support"), color="active"))
    else:
        kb.row(KeyboardButton("👤 គណនី",            emoji_id=e.get("account"), color="active"),
               KeyboardButton("💸 បញ្ចូលលុយ",       emoji_id=e.get("topup"),   color="progress"))
        kb.row(KeyboardButton("🛒 បញ្ជាទិញសេវា", emoji_id=e.get("order"), color="active"))
        kb.row(KeyboardButton("📋 ប្រវត្តិការបញ្ជាទិញ", emoji_id=e.get("history"), color="active"),
               KeyboardButton("🔍 តាមដានការបញ្ជាទិញ", emoji_id=e.get("track"),   color="active"))
        kb.row(KeyboardButton("💬 ជំនួយ", emoji_id=e.get("support"), color="active"))
    return kb

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📊 ការបញ្ជា SMM",  color="active"),
           KeyboardButton("⚙️ កំណត់ SMM API", color="progress"))
    kb.row(KeyboardButton("➕ បន្ថែម SMM",    color="active"),
           KeyboardButton("✍️ Manual SMM",   color="active"))
    kb.row(KeyboardButton("🗑️ លុប SMM",   color="danger"),
           KeyboardButton("✏️ កែ SMM",     color="progress"))
    kb.row(KeyboardButton("📦 បន្ថែម Package", color="active"),
           KeyboardButton("💰 កែតម្លៃ",       color="progress"))
    kb.row(KeyboardButton("💹 ប្រាក់ចំណេញ SMM", color="active"),
           KeyboardButton("📋 SMM Services",    color="active"))
    kb.row("━━━ 💰 ហិរញ្ញវត្ថុ ━━━")
    kb.row(KeyboardButton("💰 កាបូបលុយ",   color="active"),
           KeyboardButton("💳 ប្រាក់បញ្ញើ", color="active"))
    kb.row(KeyboardButton("💸 បន្ថែមប្រាក់", color="active"),
           KeyboardButton("💔 កាត់ប្រាក់",  color="danger"))
    kb.row(KeyboardButton("🎁 Bonus ដាក់លុយ", color="progress"))
    kb.row("━━━ 👥 អ្នកប្រើ ━━━")
    kb.row(KeyboardButton("👥 អ្នកប្រើប្រាស់", color="active"),
           KeyboardButton("📊 ស្ថិតិ",       color="active"))
    kb.row(KeyboardButton("📢 ផ្សព្វផ្សាយ", color="progress"))
    kb.row(KeyboardButton("⏱ ល្បឿន Poll",   color="progress"),
           KeyboardButton("💰 ឆែកលុយ API", color="active"))
    kb.row(KeyboardButton("🖼️ Welcome Photo", color="progress"),
           KeyboardButton("🔄 ធ្វើឱ្យទាន់សម័យ", color="progress"))
    kb.row(KeyboardButton("🔔 Notify Channel", color="progress"),
           KeyboardButton("🧪 តេស្ត Notify",   color="active"))
    kb.row("━━━ ⚙️ Settings ━━━")
    kb.row(KeyboardButton("✏️ កែ Support",      color="progress"),
           KeyboardButton("👥 Sub Admins",      color="progress"))
    kb.row(KeyboardButton("🔑 CamRapidPay Key", color="progress"),
           KeyboardButton("📝 Welcome Msg",     color="progress"))
    kb.row(KeyboardButton("😊 កំណត់ Emoji", color="progress"))
    return kb

def emoji_menu_kb():
    """Inline menu for Premium Emoji settings (replaces /setemojis, /emojilist, /emojiid)."""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✏️ កំណត់ Emoji ថ្មី", callback_data="emojimenu:set", color="progress"))
    kb.add(InlineKeyboardButton("📊 មើលស្ថានភាព",     callback_data="emojimenu:list", color="active"))
    kb.add(InlineKeyboardButton("🆔 យក Emoji ID",       callback_data="emojimenu:id", color="active"))
    return kb

def missing_emoji_kb(per_row=6):
    """Inline keyboard grid — one button per NOT-YET-SET emoji. Tapping one starts a
    single-target flow: bot remembers which char was picked, admin sends/forwards the
    premium version of it, bot matches it and saves the custom_emoji_id automatically —
    no manual ID lookup needed."""
    missing = [ch for ch, v in EMOJI_MAP.items() if not v]
    btns = []
    row = []
    for ch in missing:
        row.append(InlineKeyboardButton(ch, callback_data=f"emojipick:{ch}", color="progress"))
        if len(row) == per_row:
            btns.append(row); row = []
    if row: btns.append(row)
    btns.append([InlineKeyboardButton("📋 ផ្ញើច្រើនម្តង (Advanced)", callback_data="emojimenu:setmulti", color="active")])
    btns.append([InlineKeyboardButton("🔙 ត្រឡប់ Menu", callback_data="emojimenu:menu", color="inactive")])
    return InlineKeyboardMarkup(btns)

def sub_admin_kb():
    """Keyboard for sub-admins (limited permissions)"""
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📊 ការបញ្ជា SMM", color="active"),
           KeyboardButton("💰 កាបូបលុយ",    color="active"))
    kb.row(KeyboardButton("💳 ប្រាក់បញ្ញើ",   color="active"),
           KeyboardButton("👥 អ្នកប្រើប្រាស់", color="active"))
    kb.row(KeyboardButton("💸 បន្ថែមប្រាក់", color="active"),
           KeyboardButton("💔 កាត់ប្រាក់",   color="danger"))
    kb.row(KeyboardButton("📊 ស្ថិតិ",       color="active"),
           KeyboardButton("📢 ផ្សព្វផ្សាយ", color="progress"))
    return kb

def cancel_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("✕ Cancel", color="danger"))
    return kb

def _warm_stripped_text_map():
    """ហៅ .to_dict() លើ reply-keyboard ចម្បងទាំងអស់ (KH + EN) មួយដងពេល bot
    ចាប់ផ្ដើម ដើម្បីបំពេញ _STRIPPED_TEXT_MAP ជាមុន — កុំឲ្យមាន window ខ្លីៗ
    ចន្លោះពេល bot restart និងពេលផ្ញើ keyboard ថ្មីទៅ user ដែលអាចធ្វើឲ្យ
    ប៊ូតុងចាស់ (ដែល client នៅចាំ) ធ្លាក់ចូល fallback "មិនស្គាល់ button"។"""
    def _dump(kb):
        for row in kb.keyboard:
            for btn in row:
                if hasattr(btn, "to_dict"):
                    btn.to_dict()
    try:
        _dump(main_kb())                      # lang="kh" default
        user_lang["__warmup__"] = "en"
        _dump(main_kb(uid="__warmup__"))
        user_lang.pop("__warmup__", None)
        _dump(admin_kb())
        _dump(sub_admin_kb())
        _dump(cancel_kb())
    except Exception as e:
        logger.warning(f"⚠️ _warm_stripped_text_map failed: {e}")

def deposit_amt_kb(uid=None, promo_code=None):
    lang = get_lang(uid) if uid else "kh"
    # Preset amounts
    amounts = [1, 2, 5, 10, 20, 50]
    btns = []
    row = []
    for i, amt in enumerate(amounts):
        row.append(InlineKeyboardButton(f"💵 ${amt}", callback_data=f"dep:amt:{amt}", color="active"))
        if len(row) == 3:
            btns.append(row); row = []
    if row: btns.append(row)
    # Custom amount
    btns.append([InlineKeyboardButton(
        "✏️ ចំនួនផ្សេង" if lang=="kh" else "✏️ Custom Amount",
        callback_data="dep:custom", color="progress")])
    return InlineKeyboardMarkup(btns)

def smm_cat_kb():
    PLATFORM_ICONS = {
        "tiktok khmer": "🇰🇭",
        "tiktok": "🎵", "telegram": "📱", "facebook": "📘",
        "instagram": "📸", "youtube": "▶️", "twitter": "🐦",
        "x": "🐦", "threads": "🧵"
    }
    cats = _smm_get_categories()
    btns = []
    for cat in cats:
        icon = "📱"
        for key, ico in PLATFORM_ICONS.items():
            if key in cat.lower(): icon = ico; break
        btns.append([InlineKeyboardButton(f"{icon}  {cat}", callback_data=f"smmcat:{cat}", color="active")])
    btns.append([InlineKeyboardButton("🔙 Back", callback_data="back:main", color="inactive")])
    return InlineKeyboardMarkup(btns)

def smm_svc_kb(cat):
    SVC_ICONS = {
        "follower":"👤","like":"❤️","view":"👁️","comment":"💬",
        "share":"🔗","save":"🔖","member":"👥","subscriber":"🔔",
        "watch":"👀","reaction":"😍",
    }
    svcs = _smm_get_svcs_in_cat(cat)
    btns = []
    for slug, s in svcs:
        label = s.get("label", slug)
        icon = "⚡"
        for key, ico in SVC_ICONS.items():
            if key in label.lower(): icon = ico; break
        btns.append([InlineKeyboardButton(f"{icon}  {label}", callback_data=f"smmsvc:{slug}", color="active")])
    btns.append([InlineKeyboardButton("🔙 Back", callback_data="back:smmcats", color="inactive")])
    return InlineKeyboardMarkup(btns)

def smm_qty_kb(slug, s):
    sr    = _smm_sell_rate(s["cost_rate"], slug)
    mn    = s.get("min", 10)
    mx    = s.get("max", 100000)
    label = s.get("label", slug)
    first = label.split()[0] if label else slug
    # Flat price service — only 1 option
    if s.get("flat_price"):
        flat = float(s["flat_price"])
        btns = [[InlineKeyboardButton(
            f"✅ Order — ${flat:.2f}", callback_data=f"smmqty:{slug}:1", color="active")]]
        btns.append([InlineKeyboardButton("🔙 Back", callback_data="back:smmcats", color="inactive")])
        return InlineKeyboardMarkup(btns)
    preset = s.get("preset_qtys")
    if preset and isinstance(preset, list):
        qtys = [q for q in preset if mn <= q <= mx]
    else:
        suggestions = [100, 500, 1000, 5000, 10000, 50000]
        qtys = []
        for q in [mn] + suggestions:
            if mn <= q <= mx and q not in qtys: qtys.append(q)
            if len(qtys) >= 6: break
    btns = []
    for q in qtys:
        price = sr * q / 1000
        btns.append([InlineKeyboardButton(
            f"{q:,} {first} — ${price:.2f}", callback_data=f"smmqty:{slug}:{q}", color="active")])
    btns.append([InlineKeyboardButton("🔙 Back", callback_data="back:smmcats", color="inactive")])
    return InlineKeyboardMarkup(btns)

# ═══════════════════════════════════════════════════════════
#  USER TRACKING
# ═══════════════════════════════════════════════════════════
def _track_user(message):
    uid = message.chat.id
    uid_str = str(uid)
    u = message.from_user
    users_db[uid_str] = {
        "name":     u.first_name or "",
        "username": u.username or "",
        "last":     int(time.time()),
        "banned":   users_db.get(uid_str, {}).get("banned", False),
    }
    _save(USERS_FILE, users_db)
    wallets.setdefault(uid_str, 0.0)

def is_banned(uid):
    return bool(users_db.get(str(uid), {}).get("banned", False))

# ═══════════════════════════════════════════════════════════
#  ADMIN PROMO HELPERS
# ═══════════════════════════════════════════════════════════
def _show_promos(uid):
    if not promos:
        bot.send_message(uid, "🎟️ <b>គ្មាន Promo Code ទេ</b>", parse_mode="HTML",
                         reply_markup=admin_kb()); return
    lines = ["🎟️ <b>Promo Codes</b>\n━━━━━━━━━━━━━━━━━━"]
    for code, p in promos.items():
        dtype = f"{p['discount']:.0f}%" if p.get("pct") else f"${float(p.get('discount',0)):.2f}"
        lines.append(f"• <code>{code}</code> — {dtype} | {p.get('used',0)}/{p.get('uses',0)} used")
    bot.send_message(uid, "\n".join(lines), parse_mode="HTML")

def _utf16_slice(text, offset, length):
    """ស្រង់ substring ត្រឹមត្រូវតាម UTF-16 code units (របៀបដែល Telegram
    គិត offset/length របស់ MessageEntity — សម្រាប់ភាសាមានតួអក្សរក្រៅ BMP
    ដូច emoji, ការគណនាតាម Python string index ធម្មតាមិនត្រឹមត្រូវទេ)."""
    u = text.encode("utf-16-le")
    return u[offset * 2: (offset + length) * 2].decode("utf-16-le", errors="ignore")

def _extract_custom_emoji(src):
    """ត្រឡប់ list of (underlying_unicode_char, custom_emoji_id) ពីសារមួយ —
    underlying_unicode_char គឺជា emoji placeholder ដែលនៅពីក្រោម premium icon
    (Telegram រក្សាទុកជានិច្ច ទោះបីជាបង្ហាញ icon ផ្សេង)."""
    text = src.text or src.caption or ""
    entities = list(src.entities or []) + list(src.caption_entities or [])
    out = []
    for e in entities:
        if getattr(e, "type", None) != "custom_emoji":
            continue
        ch = _utf16_slice(text, e.offset, e.length)
        if ch:
            out.append((ch, str(e.custom_emoji_id)))
    return out

# ═══════════════════════════════════════════════════════════
#  PREMIUM EMOJI ID FINDER (admin-only utility)
#  Reply command នេះទៅសារដែលមាន premium emoji — bot បង្ហាញទាំង custom_emoji_id
#  និង unicode character ដើមដែលនៅពីក្រោម icon នីមួយៗ (មានប្រយោជន៍ដើម្បីដឹងថា
#  emoji character មួយណានៅក្នុង EMOJI_MAP ដែលនឹងត្រូវផ្គូផ្គង)។
# ═══════════════════════════════════════════════════════════
def _emojiid_text(src_msg):
    """Build the Custom Emoji ID report for a message. Returns None if none found."""
    found = _extract_custom_emoji(src_msg)
    if not found:
        return None
    lines = ["🆔 <b>Custom Emoji ID(s):</b>"]
    for i, (ch, eid) in enumerate(found, 1):
        known = "✅ មានក្នុង EMOJI_MAP" if ch in EMOJI_MAP else "⚠️ មិននៅក្នុង EMOJI_MAP"
        lines.append(f"{i}. {ch} → <code>{eid}</code> ({known})")
    return "\n".join(lines)

@bot.message_handler(commands=["emojiid"])
def cmd_emojiid(message):
    if message.from_user.id != ADMIN_ID:
        return
    src = message.reply_to_message
    if not src:
        bot.reply_to(message, "សូម Reply command នេះទៅសារដែលមាន premium emoji ជាមុនសិន។")
        return
    report = _emojiid_text(src)
    if not report:
        bot.reply_to(message, "❌ រកមិនឃើញ premium/custom emoji ក្នុងសារនោះទេ។")
        return
    bot.reply_to(message, report, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════
#  PREMIUM EMOJI AUTO-SET (admin-only) — លំដាប់ណាក៏បាន, ចាំបាច់មិនត្រូវ
#  ផ្ញើម្តងទាំងអស់ទេ (អាចធ្វើម្តងមួយៗ ឬច្រើនដងតគ្នា) ។ Reply command នេះទៅសារ
#  ណាមួយដែលមាន premium emoji — bot នឹងផ្គូផ្គង emoji ធម្មតាដែលនៅក្រោម icon
#  នីមួយៗ ទៅនឹង custom_emoji_id ស្វ័យប្រវត្តិ (មិនអាស្រ័យលំដាប់) រួច save ជា
#  អចិន្ត្រៃយ៍ទៅ EMOJI_MAP។ ធ្វើម្តងទៀតបានគ្រប់ពេលដើម្បីបន្ថែម/កែ emoji ថ្មី។
# ═══════════════════════════════════════════════════════════
def _apply_setemojis(src_msg):
    """Extract premium emoji from src_msg, apply to EMOJI_MAP, save. Returns report text, or None if no emoji found."""
    found = _extract_custom_emoji(src_msg)
    if not found:
        return None
    lines = ["✅ <b>បានកំណត់ Emoji ដោយស្វ័យប្រវត្តិ:</b>\n"]
    unknown = []
    for ch, eid in found:
        if ch in EMOJI_MAP:
            EMOJI_MAP[ch] = eid
            lines.append(f"{ch} → <code>{eid}</code>")
        else:
            unknown.append((ch, eid))
    _save(EMOJI_FILE, EMOJI_MAP)

    if unknown:
        lines.append(f"\n⚠️ {len(unknown)} emoji មិននៅក្នុងបញ្ជីស្គាល់ (បន្ថែមក្នុង EMOJI_MAP ដោយដៃបើត្រូវការ):")
        for ch, eid in unknown:
            lines.append(f"  {ch} → <code>{eid}</code>")

    remaining = sum(1 for v in EMOJI_MAP.values() if not v)
    lines.append(f"\n📊 សរុប: {sum(1 for v in EMOJI_MAP.values() if v)}/{len(EMOJI_MAP)} កំណត់រួច — នៅសល់ {remaining}")
    lines.append("🔄 Restart bot (/restart) ដើម្បីឲ្យប្រើប្រាស់ពេញលេញគ្រប់កន្លែង។")
    return "\n".join(lines)

@bot.message_handler(commands=["setemojis"])
def cmd_setemojis(message):
    if message.from_user.id != ADMIN_ID:
        return
    src = message.reply_to_message
    if not src:
        missing = [ch for ch, v in EMOJI_MAP.items() if not v]
        bot.reply_to(message,
            "សូម Reply command នេះទៅសារដែលមាន Premium Emoji (លំដាប់ណាក៏បាន, "
            "ចំនួនប៉ុន្មានក៏បាន — ធ្វើម្តងច្រើនដងក៏បាន)។\n\n"
            f"📊 កំណត់រួចហើយ: {sum(1 for v in EMOJI_MAP.values() if v)}/{len(EMOJI_MAP)}\n"
            f"នៅសល់ {len(missing)} emoji។ ប្រើ /emojilist ដើម្បីមើលបញ្ជីទាំងអស់។",
            parse_mode="HTML")
        return
    report = _apply_setemojis(src)
    if not report:
        bot.reply_to(message, "❌ រកមិនឃើញ premium/custom emoji ក្នុងសារនោះទេ។")
        return
    bot.reply_to(message, report, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════
#  PREMIUM EMOJI STATUS (admin-only) — មើលថា emoji មួយណាទាន់កំណត់ /
#  មិនទាន់កំណត់ premium icon
# ═══════════════════════════════════════════════════════════
def _emoji_status_text():
    done = [ch for ch, v in EMOJI_MAP.items() if v]
    missing = [ch for ch, v in EMOJI_MAP.items() if not v]
    lines = [f"📊 <b>Premium Emoji Status</b> — {len(done)}/{len(EMOJI_MAP)} កំណត់រួច\n"]
    if done:
        lines.append("✅ រួចហើយ: " + " ".join(done))
    if missing:
        lines.append("\n⬜ នៅសល់ (fallback ទៅ unicode ធម្មតា): " + " ".join(missing))
    return "\n".join(lines)

@bot.message_handler(commands=["emojilist"])
def cmd_emojilist(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.reply_to(message, _emoji_status_text(), parse_mode="HTML")

# ═══════════════════════════════════════════════════════════
#  START
# ═══════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.chat.id
    waiting.pop(uid, None)
    _track_user(message)
    if is_banned(uid):
        bot.send_message(uid, t(uid, "banned")); return
    if uid == ADMIN_ID:
        _multibot_hint = "\n🤖 /newbot បង្កើត Bot ថ្មី · /mybots គ្រប់គ្រង Bot រង\n" if IS_MASTER else ""
        bot.send_message(uid,
            f"🤖 <b>Panel Admin — Kaijaklike</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <code>{ADMIN_ID}</code>\n"
            f"💹 ចំណេញ SMM: <b>{_smm_profit_pct():.0f}%</b>\n"
            f"⏱ Poll: <b>{smm_poll.get('interval',5)}s</b>\n"
            f"📊 Services: <b>{len(smm_services)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━{_multibot_hint}",
            parse_mode="HTML", reply_markup=admin_kb())
        return
    if uid in sub_admins:
        bot.send_message(uid,
            f"🛡️ <b>Sub Admin Panel — Kaijaklike</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <code>{uid}</code>\n"
            f"📊 Services: <b>{len(smm_services)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML", reply_markup=sub_admin_kb())
        return
    if str(uid) not in user_lang:
        bot.send_message(uid,
            "សួស្តី! 👋 ជ្រើសភាសាដែលអ្នកចូលចិត្តសិន\n"
            "<i>Hi! Pick your language first 😊</i>",
            parse_mode="HTML", reply_markup=lang_select_kb())
        return
    _show_welcome(uid)

WELCOME_SETTINGS_FILE = _dpath("smm_welcome.json")
welcome_cfg = _load(WELCOME_SETTINGS_FILE, {"photo_id": ""})

def _save_welcome_photo(file_id):
    welcome_cfg["photo_id"] = file_id
    _save(WELCOME_SETTINGS_FILE, welcome_cfg)

def _show_welcome(uid):
    b       = bal(uid)
    custom_msg = welcome_cfg.get("custom_msg", "")
    if custom_msg:
        caption = custom_msg.format(b) if "{}" in custom_msg else custom_msg + f"\n💳 Balance: <b>${b:.2f}</b>"
    elif BOT_WELCOME_MSG:
        caption = BOT_WELCOME_MSG.format(b) if "{}" in BOT_WELCOME_MSG else BOT_WELCOME_MSG + f"\n💳 Balance: <b>${b:.2f}</b>"
    else:
        caption = t(uid, "welcome", b)
    photo_id = welcome_cfg.get("photo_id", "")
    if photo_id:
        try:
            bot.send_photo(
                uid,
                photo=photo_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=main_kb(uid)
            )
            return
        except Exception:
            pass
    # Fallback: text only
    bot.send_message(uid, caption, parse_mode="HTML", reply_markup=main_kb(uid))

# ═══════════════════════════════════════════════════════════
#  CALLBACKS
# ═══════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("setlang:"))
def cb_setlang(call):
    uid  = call.message.chat.id
    lang = call.data.split(":")[1]
    user_lang[str(uid)] = lang
    _save(LANG_FILE, user_lang)
    bot.answer_callback_query(call.id, t(uid, "lang_set"))
    try: bot.delete_message(uid, call.message.message_id)
    except: pass
    _show_welcome(uid)

@bot.callback_query_handler(func=lambda c: c.data.startswith("poll:"))
def cb_poll(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id); return
    sec = int(call.data.split(":")[1])
    smm_poll["interval"] = sec; _save(SMM_POLL_FILE, smm_poll)
    bot.answer_callback_query(call.id, f"✅ Poll = {sec}s")
    try: bot.edit_message_text(f"✅ Poll Speed = <b>{sec} វិ</b>",
                               chat_id=uid, message_id=call.message.message_id, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("depbonus:"))
def cb_depbonus(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID and uid not in sub_admins:
        bot.answer_callback_query(call.id); return
    action = call.data.split(":", 1)[1]
    if action == "toggle":
        dep_bonus_cfg["enabled"] = not dep_bonus_cfg.get("enabled", True)
        _save(DEP_BONUS_FILE, dep_bonus_cfg)
        bot.answer_callback_query(call.id, "✅ បានប្តូរស្ថានភាព")
        btns = InlineKeyboardMarkup()
        toggle_label = "🔴 បិទ Auto Bonus" if dep_bonus_cfg.get("enabled", True) else "🟢 បើក Auto Bonus"
        btns.add(InlineKeyboardButton(toggle_label, callback_data="depbonus:toggle",
                                      color=("danger" if dep_bonus_cfg.get("enabled", True) else "active")))
        btns.add(InlineKeyboardButton("✏️ កែ % / ចំនួនអប្បបរមា", callback_data="depbonus:edit", color="progress"))
        try:
            bot.edit_message_text(
                f"{_dep_bonus_status_text()}\n━━━━━━━━━━━━━━━━━━\n"
                f"👉 អ្នកប្រើដាក់លុយចាប់ពី <b>${float(dep_bonus_cfg.get('min_amount',1.0)):.2f}</b> ឡើងទៅ "
                f"នឹងទទួល Bonus <b>{float(dep_bonus_cfg.get('pct',5.0)):.0f}%</b> បញ្ចូល Balance ដោយស្វ័យប្រវត្តិ "
                f"(បូកបន្ថែមលើ Promo Code ប្រសិនបើមាន)។",
                chat_id=uid, message_id=call.message.message_id, parse_mode="HTML", reply_markup=btns)
        except: pass
        return
    if action == "edit":
        bot.answer_callback_query(call.id)
        waiting[uid] = {"step": "depbonus_edit"}
        bot.send_message(uid,
            f"✏️ <b>កែ Bonus ដាក់លុយ</b>\n"
            f"បច្ចុប្បន្ន: ចាប់ពី ${float(dep_bonus_cfg.get('min_amount',1.0)):.2f} → {float(dep_bonus_cfg.get('pct',5.0)):.0f}%\n\n"
            f"ផ្ញើជា <code>ចំនួនអប្បបរមា,ភាគរយ</code>\nឧ: <code>1,5</code> (ដាក់ $1 ឡើងទៅ ទទួល 5%)",
            parse_mode="HTML", reply_markup=cancel_kb())
        return

@bot.callback_query_handler(func=lambda c: c.data.startswith("dep:"))
def cb_dep(call):
    uid     = call.message.chat.id
    uid_str = str(uid)
    lang    = get_lang(uid)
    val     = call.data[4:]
    bot.answer_callback_query(call.id)

    # ── ជ្រើស amount preset ──
    if val.startswith("amt:"):
        amount = float(val.split(":")[1])
        waiting.pop(uid, None)
        _process_deposit(uid, uid_str, amount, None)
        return

    # ── custom amount ──
    if val == "custom":
        waiting[uid] = {"step": "dep_custom_amt"}
        bot.send_message(uid,
            "✏️ <b>វាយចំនួន (USD):</b>\nឧ: <code>3</code> ឬ <code>7.50</code>" if lang=="kh" else
            "✏️ <b>Enter amount (USD):</b>\ne.g. <code>3</code> or <code>7.50</code>",
            parse_mode="HTML", reply_markup=cancel_kb())
        return

@bot.callback_query_handler(func=lambda c: c.data.startswith("back:"))
def cb_back(call):
    uid  = call.message.chat.id
    dest = call.data[5:]
    bot.answer_callback_query(call.id)
    waiting.pop(uid, None)
    if dest == "main":
        try: bot.delete_message(uid, call.message.message_id)
        except: pass
        _show_welcome(uid)
    elif dest == "smmcats":
        try:
            bot.edit_message_text("📊 <b>SMM Services</b>\n━━━━━━━━━━━━━━━━━━\nជ្រើស Platform:",
                                  chat_id=uid, message_id=call.message.message_id,
                                  parse_mode="HTML", reply_markup=smm_cat_kb())
        except:
            bot.send_message(uid, "📊 <b>SMM Services</b>",
                             parse_mode="HTML", reply_markup=smm_cat_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("smmcat:"))
def cb_smmcat(call):
    uid = call.message.chat.id
    cat = call.data[7:]
    bot.answer_callback_query(call.id)
    svcs = _smm_get_svcs_in_cat(cat)
    if not svcs:
        try: bot.answer_callback_query(call.id, "❌ គ្មាន Service", show_alert=True)
        except: pass
        return
    is_tiktok_khmer = "tiktok khmer" in cat.lower()
    if is_tiktok_khmer:
        header = (
            f"🇰🇭 <b>TikTok Khmer Services!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"• ធានាបានអ្នកមើលខ្មែរ 100%\n"
            f"• អាចបានលើសទៅតាមវីដេអូ\n\n"
            f"ជ្រើសសេវាកម្ម:"
        )
    else:
        header = f"📂 <b>{cat}</b>\n━━━━━━━━━━━━━━━━━━\nជ្រើស Service:"
    try:
        bot.edit_message_text(header,
                              chat_id=uid, message_id=call.message.message_id,
                              parse_mode="HTML", reply_markup=smm_svc_kb(cat))
    except:
        bot.send_message(uid, header, parse_mode="HTML", reply_markup=smm_svc_kb(cat))

@bot.callback_query_handler(func=lambda c: c.data.startswith("smmsvc:"))
def cb_smmsvc(call):
    uid  = call.message.chat.id
    slug = call.data[7:]
    bot.answer_callback_query(call.id)
    s = smm_services.get(slug)
    if not s: return
    sr   = _smm_sell_rate(s["cost_rate"], slug)
    lang = get_lang(uid)
    # Price display
    if s.get("flat_price"):
        price_line = f"💰 តម្លៃ: <b>${float(s['flat_price']):.2f} / order</b>"
    else:
        price_line = f"💰 {'តម្លៃ' if lang=='kh' else 'Price'}: <b>${sr:.2f}/1K</b>\n📏 Min: {s.get('min',10):,}  ·  Max: {s.get('max',100000):,}"
    desc_line = f"\n📋 {s['description']}" if s.get("description") else ""
    txt  = (f"⚡ <b>{s.get('label',slug)}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{price_line}"
            f"{desc_line}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{'ជ្រើស Quantity:' if lang=='kh' else 'Choose Quantity:'}")
    try:
        bot.edit_message_text(txt, chat_id=uid, message_id=call.message.message_id,
                              parse_mode="HTML", reply_markup=smm_qty_kb(slug, s))
    except:
        bot.send_message(uid, txt, parse_mode="HTML", reply_markup=smm_qty_kb(slug, s))

@bot.callback_query_handler(func=lambda c: c.data.startswith("smmqty:"))
def cb_smmqty(call):
    uid = call.message.chat.id
    bot.answer_callback_query(call.id)
    parts = call.data.split(":")
    slug  = parts[1]; qty = int(parts[2])
    s     = smm_services.get(slug)
    if not s: return
    price = _smm_price_for_order(slug, qty)
    lang  = get_lang(uid)
    is_tiktok_promote = s.get("flat_price") and "tiktok" in slug.lower()
    if is_tiktok_promote:
        link_prompt = (
            f"🔗 <b>ផ្ញើ Link វីដេអូ TikTok:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 {s.get('label',slug)}\n"
            f"💰 តម្លៃ: <b>${price:.2f}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>សំខាន់!</b> បន្ទាប់ពី order:\n"
            f"1️⃣ ចូល TikTok Inbox\n"
            f"2️⃣ System notifications → Promote Assistant\n"
            f"3️⃣ ចុច <b>Respond</b> → <b>Authorize</b> → <b>Confirm</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📎 ឧ: <code>https://www.tiktok.com/@user/video/123</code>"
        )
    else:
        link_prompt = (
            f"🔗 <b>{'ផ្ញើ Link:' if lang=='kh' else 'Send Link:'}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 {s.get('label',slug)}\n"
            f"💰 {qty:,} — <b>${price:.4f}</b>"
        )
    waiting[uid] = {"step": "smm_link", "slug": slug, "qty": qty, "price": price}
    try:
        bot.edit_message_text(
            link_prompt,
            chat_id=uid, message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="back:main", color="inactive")]]))
    except:
        bot.send_message(uid, link_prompt, parse_mode="HTML", reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("smmapi:"))
def cb_smmapi(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: return
    action = call.data[7:]
    bot.answer_callback_query(call.id)

    if action == "setup":
        waiting[uid] = "smm_api_url"
        bot.send_message(uid,
            "🌐 <b>ផ្ញើ SMM API URL</b>\nឧ: <code>https://smmking.net/api/v2</code>",
            parse_mode="HTML", reply_markup=cancel_kb())

    elif action == "test":
        url = smm_api.get("url",""); key = smm_api.get("key","")
        if not url or not key:
            bot.send_message(uid, "❌ API មិនទាន់ set!", reply_markup=admin_kb()); return
        try:
            r = http.post(url, data={"key": key, "action": "balance"}, timeout=10)
            d = r.json()
            balance  = d.get("balance", d.get("Balance", "?"))
            currency = d.get("currency", d.get("Currency", "USD"))
            bot.send_message(uid,
                f"✅ <b>Connection OK!</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"💰 Balance: <b>{balance} {currency}</b>",
                parse_mode="HTML", reply_markup=admin_kb())
        except Exception as e:
            bot.send_message(uid, f"❌ Connection failed: <code>{e}</code>",
                             parse_mode="HTML", reply_markup=admin_kb())

    elif action == "clear":
        smm_api.clear(); smm_api.update({"url":"","key":""})
        _save(SMM_API_FILE, smm_api)
        bot.send_message(uid, "🗑️ SMM API cleared!", reply_markup=admin_kb())

# ── Admin: Confirm / Reject deposit ──
@bot.callback_query_handler(func=lambda c: c.data.startswith("admconf:"))
def cb_admconf(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id); return
    dep_id = call.data[8:]
    dep    = smm_deps.get(dep_id)
    if not dep or dep.get("status") != "pending":
        bot.answer_callback_query(call.id, "⚠️ Deposit មិន pending ទេ", show_alert=True); return
    bot.answer_callback_query(call.id)
    # Ask admin for amount
    waiting[uid] = {"step": "adm_confirm_dep", "dep_id": dep_id}
    bot.send_message(uid,
        f"💰 <b>Enter amount received (USD):</b>\n"
        f"📌 Ref: <code>{dep.get('reference','')}</code>\n"
        f"👤 User: <code>{dep.get('uid','')}</code>",
        parse_mode="HTML", reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("admrej:"))
def cb_admrej(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id); return
    dep_id = call.data[7:]
    dep    = smm_deps.get(dep_id)
    if not dep:
        bot.answer_callback_query(call.id, "❌ Deposit រកមិនឃើញ", show_alert=True); return
    bot.answer_callback_query(call.id)
    dep["status"] = "rejected"; _save(SMM_DEP_FILE, smm_deps)
    try:
        bot.edit_message_text(
            f"❌ <b>Deposit Rejected</b>\n📌 Ref: <code>{dep.get('reference','')}</code>",
            chat_id=uid, message_id=call.message.message_id, parse_mode="HTML")
    except: pass
    try:
        bot.send_message(int(dep["uid"]),
            "❌ <b>ការ Deposit ត្រូវបាន Reject!</b>\nទំនាក់ Admin: @KhmerSmm099",
            parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("mansvc_cat:"))
def cb_mansvc_cat(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id); return
    cat = call.data[len("mansvc_cat:"):]
    bot.answer_callback_query(call.id)
    step = waiting.get(uid, {})
    label = step.get("label", "") if isinstance(step, dict) else ""
    if cat == "__custom__":
        waiting[uid] = {"step": "manual_svc_cat_custom", "label": label}
        bot.send_message(uid,
            "✏️ <b>វាយ Category ផ្ទាល់ខ្លួន:</b>\nឧ: <code>TikTok Khmer</code>",
            parse_mode="HTML", reply_markup=cancel_kb())
    else:
        waiting[uid] = {"step": "manual_svc_price", "label": label, "cat": cat}
        bot.send_message(uid,
            f"💰 <b>ដាក់តម្លៃ (USD per 1000)</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📂 Category: <b>{cat}</b>\n"
            f"📝 ឈ្មោះ: <b>{label}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"ឧ: <code>0.50</code> = $0.50 per 1K\n"
            f"ឧ: <code>1.20</code> = $1.20 per 1K",
            parse_mode="HTML", reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("pkgcat:"))
def cb_pkgcat(call):
    """Admin: choose category for a new flat-price Package"""
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id); return
    cat = call.data[len("pkgcat:"):]
    bot.answer_callback_query(call.id)
    step = waiting.get(uid, {})
    label = step.get("label", "") if isinstance(step, dict) else ""
    if cat == "__custom__":
        waiting[uid] = {"step": "pkg_cat_custom", "label": label}
        bot.send_message(uid,
            "✏️ <b>វាយ Category ផ្ទាល់ខ្លួន:</b>\nឧ: <code>TikTok Khmer</code>",
            parse_mode="HTML", reply_markup=cancel_kb())
    else:
        waiting[uid] = {"step": "pkg_desc", "label": label, "cat": cat}
        bot.send_message(uid,
            f"📂 Category: <b>{cat}</b>\n📝 ឈ្មោះ: <b>{label}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>ការពិពណ៌នា Package (Description)</b>\n"
            f"ឧ: <code>1K-2K Likes ❤️ + 3.5K Views 👁</code>\n"
            f"ឬ វាយ <code>-</code> ដើម្បីរំលង",
            parse_mode="HTML", reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("editprice:"))
def cb_editprice(call):
    """Admin: edit the price of an existing service/package"""
    uid = call.message.chat.id
    if uid != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    slug = call.data[len("editprice:"):]
    s = smm_services.get(slug)
    if not s:
        bot.send_message(uid, "❌ Service រកមិនឃើញ", reply_markup=admin_kb()); return
    waiting[uid] = {"step": "edit_svc_price", "slug": slug}
    if s.get("flat_price"):
        cur = f"${float(s['flat_price']):.2f} / order"
    else:
        cur = f"${float(s.get('cost_rate',0)):.2f} / 1K"
    bot.send_message(uid,
        f"💰 <b>កែតម្លៃ</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 {s.get('label', slug)}\n"
        f"💵 តម្លៃបច្ចុប្បន្ន: <b>{cur}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"វាយ <b>តម្លៃថ្មី</b> (លេខទទេ):",
        parse_mode="HTML", reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("manord:"))
def cb_manord(call):
    """Admin: mark manual order as completed"""
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id); return
    parts = call.data.split(":")
    action = parts[1]
    oid    = parts[2] if len(parts) > 2 else ""
    bot.answer_callback_query(call.id)
    o = smm_orders.get(oid)
    if not o:
        bot.send_message(uid, f"❌ Order <code>{oid}</code> រកមិនឃើញ",
                         parse_mode="HTML"); return
    if action == "done":
        waiting[uid] = {"step": "manual_order_done", "oid": oid, "user_uid": o["uid"]}
        bot.send_message(uid,
            f"✅ <b>Complete Order</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <code>{oid}</code>\n"
            f"👤 User: <code>{o['uid']}</code>\n"
            f"📊 {o.get('label','?')} × {o.get('qty',0):,}\n"
            f"🔗 <code>{o.get('link','?')}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>វាយ Note ឲ្យ User</b> (ឬ <code>-</code> ដើម្បីរំលង):",
            parse_mode="HTML", reply_markup=cancel_kb())
    elif action == "reject":
        smm_orders[oid]["status"] = "rejected"
        _save(SMM_ORD_FILE, smm_orders)
        try:
            bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=None)
        except: pass
        try:
            bot.send_message(int(o["uid"]),
                f"❌ <b>Order ត្រូវបាន Reject!</b>\n"
                f"🆔 <code>{oid}</code>\n"
                f"💳  លុយបានដក (${ o.get('price',0):.4f}) ត្រូវបានសងវិញ\n"
                f"ទំនាក់ Admin ប្រសិនបើចង់ដឹង: @smos_sne1",
                parse_mode="HTML")
            # Refund
            add_bal(int(o["uid"]), float(o.get("price") or 0))
        except: pass
        bot.send_message(uid,
            f"❌ <b>Rejected & Refunded</b>\n🆔 <code>{oid}</code>",
            parse_mode="HTML", reply_markup=admin_kb())


@bot.callback_query_handler(func=lambda c: c.data.startswith("editsvc:"))
def cb_editsvc(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    slug = call.data[len("editsvc:"):]
    s = smm_services.get(slug)
    if not s:
        bot.send_message(uid, "❌ Service រកមិនឃើញ", reply_markup=admin_kb()); return
    old_label = s.get("label", slug)
    api_id    = s.get("api_id", "?")
    waiting[uid] = {"step": "edit_svc_name", "slug": slug}
    bot.send_message(uid,
        f"✏️ <b>កែឈ្មោះ Service</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 API ID: <code>{api_id}</code>\n"
        f"📝 ឈ្មោះ​បច្ចុប្បន្ន:\n<b>{old_label}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"វាយ <b>ឈ្មោះថ្មី</b>:",
        parse_mode="HTML", reply_markup=cancel_kb())


@bot.callback_query_handler(func=lambda c: c.data.startswith("smmaddcat:"))
def cb_smmaddcat(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: return
    cat = call.data[len("smmaddcat:"):]
    bot.answer_callback_query(call.id)
    if cat == "custom":
        waiting[uid] = "smm_add_cat"
        bot.send_message(uid, "✏️ វាយ Category name (ឧ: TikTok Live, Spotify):",
                         reply_markup=cancel_kb())
    else:
        waiting[uid] = {"step": "smm_add_ids", "cat": cat}
        bot.send_message(uid,
            f"📂 Category: <b>{cat}</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"ផ្ញើ Service IDs (comma separated):\n"
            f"ឧ: <code>5441,5448,5502</code>\n\n"
            f"💡 IDs រក នៅ SMM Panel → Services",
            parse_mode="HTML", reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("delsvc:"))
def cb_delsvc(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    parts = call.data.split(":", 2)

    if len(parts) == 3 and parts[1] == "cat":
        cat = parts[2]
        to_del = [slug for slug, s in smm_services.items() if s.get("category") == cat]
        for slug in to_del:
            smm_services.pop(slug, None)
        _save(SMM_SVC_FILE, smm_services)
        try: bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=None)
        except: pass
        bot.send_message(uid,
            f"✅ Deleted <b>{len(to_del)}</b> services in <b>{cat}</b>",
            parse_mode="HTML", reply_markup=admin_kb())
        return

    slug = parts[1]
    s    = smm_services.get(slug)
    if not s:
        bot.send_message(uid, "❌ Service រកមិនឃើញ", reply_markup=admin_kb()); return
    label  = s.get("label", slug)
    api_id = s.get("api_id", "?")
    smm_services.pop(slug, None)
    _save(SMM_SVC_FILE, smm_services)
    try: bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=None)
    except: pass
    bot.send_message(uid,
        f"✅ Deleted: <b>[{api_id}] {label}</b>\n"
        f"📊 Remaining: <b>{len(smm_services)}</b>",
        parse_mode="HTML", reply_markup=admin_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("useraction:"))
def cb_useraction(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    parts  = call.data.split(":")
    action = parts[1]
    target = parts[2] if len(parts) > 2 else ""

    if action == "addbal":
        waiting[uid] = {"step": "add_balance_amt", "target": target}
        bot.send_message(uid,
            f"💸 <b>បន្ថែមប្រាក់</b>\n👤 UID: <code>{target}</code>\n"
            f"💳 Balance: <b>${bal(int(target)):.2f}</b>\nផ្ញើ Amount $:",
            parse_mode="HTML", reply_markup=cancel_kb())

    elif action == "dedbal":
        waiting[uid] = {"step": "deduct_balance_amt", "target": target}
        bot.send_message(uid,
            f"💔 <b>កាត់ប្រាក់</b>\n👤 UID: <code>{target}</code>\n"
            f"💳 Balance: <b>${bal(int(target)):.2f}</b>\nផ្ញើ Amount $ ដក:",
            parse_mode="HTML", reply_markup=cancel_kb())

    elif action == "ban":
        users_db[target]["banned"] = True; _save(USERS_FILE, users_db)
        bot.send_message(uid, f"🚫 Banned <code>{target}</code>",
                         parse_mode="HTML", reply_markup=admin_kb())

    elif action == "unban":
        users_db[target]["banned"] = False; _save(USERS_FILE, users_db)
        bot.send_message(uid, f"🔓 Unbanned <code>{target}</code>",
                         parse_mode="HTML", reply_markup=admin_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("adminpromo:"))
def cb_adminpromo(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    action = call.data[len("adminpromo:"):]
    if action == "add":
        waiting[uid] = "promo_add_code"
        bot.send_message(uid,
            "🎟️ <b>បន្ថែម Promo Code</b>\n━━━━━━━━━━━━━━━━━━\n"
            "Format: <code>CODE DISCOUNT TYPE USES</b></code>\n\n"
            "TYPE: <code>pct</code> (%) ឬ <code>fix</code> ($)\n\n"
            "ឧទាហរណ៍:\n"
            "<code>SAVE50 50 pct 100</code>  → 50% off, 100 uses\n"
            "<code>GIFT1 1.00 fix 50</code>  → $1 bonus, 50 uses",
            parse_mode="HTML", reply_markup=cancel_kb())
    elif action == "list":
        _show_promos(uid)

# ═══════════════════════════════════════════════════════════
#  /newbot CONFIRMATION + CLONE MANAGEMENT CALLBACKS
# ═══════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "newbot_confirm_yes")
def cb_newbot_confirm_yes(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID or not IS_MASTER:
        bot.answer_callback_query(call.id, "🚫 គ្មានសិទ្ធិ"); return
    step = waiting.get(uid)
    if not isinstance(step, dict) or step.get("step") != "newbot_confirm":
        bot.answer_callback_query(call.id, "Session ផុតកំណត់"); return
    name = step["name"]
    cfg = {
        "token": step["token"],
        "admin_id": step["new_admin_id"],
        "camrapid_key": step["camrapid_key"],
        "port": step["port"],
        "display_name": step.get("display_name", step["name"]),
        "welcome_msg":  step.get("welcome_msg", ""),
    }
    clone_registry[name] = cfg
    _save(CLONES_REGISTRY, clone_registry)
    waiting.pop(uid, None)
    bot.answer_callback_query(call.id, "កំពុងបង្កើត...")
    try:
        _spawn_clone(name, cfg)
        bot.send_message(uid,
            f"🎉 បានបង្កើត Bot '<b>{name}</b>' ជោគជ័យ ហើយកំពុងដំណើរការ!\n"
            f"មាន feature ដូចគ្នា ១០០% ជា bot នេះ តែទិន្នន័យដាច់ដោយឡែកទាំងស្រុង។\n"
            f"ប្រើ /mybots ដើម្បីគ្រប់គ្រង។",
            parse_mode="HTML", reply_markup=admin_kb())
    except Exception as e:
        bot.send_message(uid, f"❌ បង្កើតមិនជោគជ័យ: {e}", reply_markup=admin_kb())

@bot.callback_query_handler(func=lambda c: c.data == "newbot_confirm_no")
def cb_newbot_confirm_no(call):
    uid = call.message.chat.id
    waiting.pop(uid, None)
    bot.answer_callback_query(call.id, "បានបោះបង់")
    bot.send_message(uid, "❌ បានបោះបង់ការបង្កើត bot ថ្មី។", reply_markup=admin_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("cln_view|"))
def cb_cln_view(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID or not IS_MASTER:
        bot.answer_callback_query(call.id, "🚫 គ្មានសិទ្ធិ"); return
    name = call.data.split("|", 1)[1]
    cfg = clone_registry.get(name)
    if not cfg:
        bot.answer_callback_query(call.id, "រកមិនឃើញ"); return
    bot.answer_callback_query(call.id)
    status = "🟢 កំពុងដំណើរការ" if _clone_is_running(name) else "🔴 បិទ"
    masked = cfg["token"][:10] + "..." + cfg["token"][-4:]
    text = (f"🤖 <b>{name}</b>\nស្ថានភាព: {status}\n"
            f"Admin ID: <code>{cfg['admin_id']}</code>\nToken: <code>{masked}</code>\n"
            f"Port: <code>{cfg['port']}</code>")
    kb = InlineKeyboardMarkup(row_width=2)
    if _clone_is_running(name):
        kb.add(InlineKeyboardButton("🛑 បិទ", callback_data=f"cln_stop|{name}", color="inactive"),
               InlineKeyboardButton("🔄 Restart", callback_data=f"cln_restart|{name}", color="progress"))
    else:
        kb.add(InlineKeyboardButton("▶️ ដំណើរការ", callback_data=f"cln_start|{name}", color="active"))
    kb.add(InlineKeyboardButton("🗑️ លុប", callback_data=f"cln_delete|{name}", color="inactive"))
    kb.add(InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="cln_list", color="inactive"))
    bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "cln_list")
def cb_cln_list(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID or not IS_MASTER:
        bot.answer_callback_query(call.id, "🚫 គ្មានសិទ្ធិ"); return
    bot.answer_callback_query(call.id)
    if not clone_registry:
        bot.send_message(uid, "📭 មិនទាន់មាន Bot រងណាមួយទេ។", reply_markup=admin_kb()); return
    kb = InlineKeyboardMarkup(row_width=1)
    for nm in clone_registry:
        st = "🟢" if _clone_is_running(nm) else "🔴"
        kb.add(InlineKeyboardButton(f"{st} {nm}", callback_data=f"cln_view|{nm}", color="default"))
    bot.send_message(uid, "📋 <b>Bot រងទាំងអស់</b>", parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("cln_start|", "cln_stop|", "cln_restart|", "cln_delete|")))
def cb_cln_actions(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID or not IS_MASTER:
        bot.answer_callback_query(call.id, "🚫 គ្មានសិទ្ធិ"); return
    action, name = call.data.split("|", 1)
    cfg = clone_registry.get(name)
    if not cfg:
        bot.answer_callback_query(call.id, "រកមិនឃើញ"); return

    if action == "cln_start":
        _spawn_clone(name, cfg)
        bot.answer_callback_query(call.id, "ដំណើរការ...")
        bot.send_message(uid, f"✅ ដំណើរការ '{name}' ជោគជ័យ")
    elif action == "cln_stop":
        _stop_clone(name)
        bot.answer_callback_query(call.id, "បានបិទ")
        bot.send_message(uid, f"🛑 បានបិទ '{name}'")
    elif action == "cln_restart":
        _stop_clone(name); time.sleep(1); _spawn_clone(name, cfg)
        bot.answer_callback_query(call.id, "Restarting...")
        bot.send_message(uid, f"🔄 បាន restart '{name}'")
    elif action == "cln_delete":
        _stop_clone(name)
        clone_registry.pop(name, None)
        _save(CLONES_REGISTRY, clone_registry)
        bot.answer_callback_query(call.id, "បានលុប")
        bot.send_message(uid, f"🗑 បានលុប '{name}' ចេញពី registry (ទិន្នន័យ bot_clones/{name}/ នៅសល់)")
        return
    bot.send_message(uid, f"ស្ថានភាព '{name}':")
    cb_cln_view_inline = InlineKeyboardMarkup(row_width=2)
    if _clone_is_running(name):
        cb_cln_view_inline.add(InlineKeyboardButton("🛑 បិទ", callback_data=f"cln_stop|{name}", color="inactive"),
                                InlineKeyboardButton("🔄 Restart", callback_data=f"cln_restart|{name}", color="progress"))
    else:
        cb_cln_view_inline.add(InlineKeyboardButton("▶️ ដំណើរការ", callback_data=f"cln_start|{name}", color="active"))
    cb_cln_view_inline.add(InlineKeyboardButton("🗑️ លុប", callback_data=f"cln_delete|{name}", color="inactive"))
    bot.send_message(uid, f"🤖 {name}", reply_markup=cb_cln_view_inline)

# ═══════════════════════════════════════════════════════════
#  SETTINGS CALLBACKS — Support / Sub Admin / CamRapidPay / Welcome
# ═══════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_support:"))
def cb_set_support(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id, "🚫"); return
    lang = call.data.split(":")[1]
    bot.answer_callback_query(call.id)
    waiting[uid] = {"step": "set_support_text", "lang": lang}
    bot.send_message(uid,
        f"✏️ <b>វាយ Support Message {'(ខ្មែរ)' if lang=='kh' else '(English)'}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 HTML tags អនុញ្ញាត: <code>&lt;b&gt;</code>, <code>&lt;i&gt;</code>, <code>&lt;code&gt;</code>\n"
        f"ឬផ្ញើ <code>-</code> ដើម្បី reset ទៅ default:",
        parse_mode="HTML", reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("subadmin:"))
def cb_subadmin(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id, "🚫"); return
    action = call.data.split(":")[1]
    bot.answer_callback_query(call.id)
    if action == "add":
        waiting[uid] = "subadmin_add_id"
        bot.send_message(uid,
            "➕ <b>បន្ថែម Sub Admin</b>\n━━━━━━━━━━━━━━━━━━\nផ្ញើ Telegram ID (លេខ) របស់ Sub Admin:",
            parse_mode="HTML", reply_markup=cancel_kb())
    elif action == "list_del":
        if not sub_admins:
            bot.send_message(uid, "📭 គ្មាន Sub Admin ទេ", reply_markup=admin_kb()); return
        kb2 = InlineKeyboardMarkup(row_width=1)
        for sa in sub_admins:
            kb2.add(InlineKeyboardButton(f"🗑️ លុប {sa}", callback_data=f"subadmin:del:{sa}", color="inactive"))
        bot.send_message(uid, "👥 <b>ជ្រើស Sub Admin ដើម្បីលុប:</b>",
                         parse_mode="HTML", reply_markup=kb2)
    else:
        # del:<id>
        parts = call.data.split(":")
        if len(parts) == 3:
            del_id = int(parts[2])
            if del_id in sub_admins:
                sub_admins.remove(del_id)
                _save(SUB_ADMIN_FILE, sub_admins)
            bot.send_message(uid, f"✅ លុប Sub Admin <code>{del_id}</code> ចេញ",
                             parse_mode="HTML", reply_markup=admin_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_camrapid:"))
def cb_set_camrapid(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id, "🚫"); return
    action = call.data.split(":")[1]
    bot.answer_callback_query(call.id)
    if action == "edit":
        waiting[uid] = "set_camrapid_key"
        bot.send_message(uid,
            "🔑 <b>ផ្ញើ CamRapidPay API Key ថ្មី:</b>\n"
            "ឬផ្ញើ <code>-</code> ដើម្បី reset ទៅ env/default",
            parse_mode="HTML", reply_markup=cancel_kb())
    elif action == "test":
        key = _effective_camrapid_key()
        try:
            r = http.get(CAMRAPID_CHECK, params={"api_key": key, "reference": "test_ping"}, timeout=10)
            d = r.json()
            ok = r.status_code < 500
            bot.send_message(uid,
                f"{'✅' if ok else '❌'} <b>CamRapidPay Test</b>\n"
                f"Status: <b>{r.status_code}</b>\n"
                f"Response: <code>{str(d)[:200]}</code>",
                parse_mode="HTML", reply_markup=admin_kb())
        except Exception as e:
            bot.send_message(uid, f"❌ Test failed: <code>{e}</code>",
                             parse_mode="HTML", reply_markup=admin_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_welcome:"))
def cb_set_welcome(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID: bot.answer_callback_query(call.id, "🚫"); return
    action = call.data.split(":")[1]
    bot.answer_callback_query(call.id)
    if action == "text":
        waiting[uid] = "set_welcome_msg_text"
        bot.send_message(uid,
            "📝 <b>វាយ Welcome Message ថ្មី:</b>\n"
            "💡 ប្រើ <code>{}</code> ដើម្បីដាក់ balance\n"
            "ឬផ្ញើ <code>-</code> ដើម្បី reset ទៅ default:",
            parse_mode="HTML", reply_markup=cancel_kb())
    elif action == "reset":
        welcome_cfg.pop("custom_msg", None)
        _save(WELCOME_SETTINGS_FILE, welcome_cfg)
        bot.send_message(uid, "✅ Welcome Message reset ទៅ default!", reply_markup=admin_kb())
# ═══════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("emojimenu:"))
def cb_emojimenu(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID:
        bot.answer_callback_query(call.id, "🚫 Master Admin only!"); return
    action = call.data.split(":", 1)[1]
    bot.answer_callback_query(call.id)
    if action == "set":
        waiting.pop(uid, None)   # ជម្រះ state ចាស់ ពេលបើក grid ថ្មី
        missing = [ch for ch, v in EMOJI_MAP.items() if not v]
        if not missing:
            bot.send_message(uid, "🎉 <b>Emoji ទាំងអស់បានកំណត់រួច 100% ហើយ!</b>",
                parse_mode="HTML", reply_markup=admin_kb()); return
        bot.send_message(uid,
            "✏️ <b>ជ្រើស Emoji ដែលចង់កំណត់</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "👇 ចុចលើ emoji ណាមួយខាងក្រោម រួចផ្ញើ ឬ Forward Premium version របស់វា\n"
            "<i>bot នឹងចាប់យក custom_emoji_id ដោយស្វ័យប្រវត្តិ — មិនចាំបាច់ដឹង ID ដោយខ្លួនឯងទេ</i>\n\n"
            f"📊 កំណត់រួច: {sum(1 for v in EMOJI_MAP.values() if v)}/{len(EMOJI_MAP)} — នៅសល់ {len(missing)}",
            parse_mode="HTML", reply_markup=missing_emoji_kb())
    elif action == "menu":
        waiting.pop(uid, None)   # ជម្រះ state ចាស់ (ដូចជា await_setemoji_single) បើនៅសល់
        done_n = sum(1 for v in EMOJI_MAP.values() if v)
        bot.send_message(uid,
            f"😊 <b>Premium Emoji Settings</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"កំណត់រួច: <b>{done_n}/{len(EMOJI_MAP)}</b>\n\n"
            f"ជ្រើសសកម្មភាព:",
            parse_mode="HTML", reply_markup=emoji_menu_kb())
    elif action == "setmulti":
        waiting[uid] = "await_setemojis"
        missing = [ch for ch, v in EMOJI_MAP.items() if not v]
        preview = " ".join(missing[:40]) + (" ..." if len(missing) > 40 else "")
        bot.send_message(uid,
            "📋 <b>កំណត់ Emoji ច្រើនម្តង (Advanced)</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📤 ផ្ញើ ឬ Forward សារដែលមាន Premium Emoji ច្រើនក្នុងសារតែមួយ\n"
            "<i>(លំដាប់ណាក៏បាន — ផ្ញើជាប់ៗគ្នាបានច្រើនសារដោយមិនចាំបាច់ចុច Menu ម្តងទៀត)</i>\n\n"
            f"📊 កំណត់រួចហើយ: {sum(1 for v in EMOJI_MAP.values() if v)}/{len(EMOJI_MAP)} — នៅសល់ {len(missing)}\n"
            + (f"⬜ នៅសល់: {preview}\n\n" if missing else "\n") +
            "✕ Cancel ពេលរួចរាល់",
            parse_mode="HTML", reply_markup=cancel_kb())
    elif action == "list":
        bot.send_message(uid, _emoji_status_text(), parse_mode="HTML", reply_markup=admin_kb())
    elif action == "id":
        waiting[uid] = "await_emojiid"
        bot.send_message(uid,
            "🆔 <b>យក Emoji ID</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📤 ផ្ញើ ឬ Forward សារដែលមាន Premium Emoji មកទីនេះ",
            parse_mode="HTML", reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("emojipick:"))
def cb_emojipick(call):
    uid = call.message.chat.id
    if uid != ADMIN_ID:
        bot.answer_callback_query(call.id, "🚫 Master Admin only!"); return
    ch = call.data.split(":", 1)[1]
    if ch not in EMOJI_MAP:
        bot.answer_callback_query(call.id, "❌ Emoji នេះលែងមាន!"); return
    bot.answer_callback_query(call.id)
    waiting[uid] = {"step": "await_setemoji_single", "char": ch}
    bot.send_message(uid,
        f"✏️ <b>កំណត់ Premium Emoji សម្រាប់ {ch}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📤 ផ្ញើ ឬ Forward សារដែលមាន Premium version របស់ {ch} ចូលទីនេះ\n"
        f"<i>bot នឹងចាប់យក ID ដោយស្វ័យប្រវត្តិ ហើយភ្ជាប់ទៅ {ch} ភ្លាមៗ</i>",
        parse_mode="HTML", reply_markup=cancel_kb())

def _do_broadcast(admin_uid, message):
    waiting.pop(admin_uid, None)
    sent = failed = 0
    for u_id in list(users_db.keys()):
        try:
            if message.photo:
                bot.send_photo(int(u_id), message.photo[-1].file_id, caption=message.caption or "")
            elif message.video:
                bot.send_video(int(u_id), message.video.file_id, caption=message.caption or "")
            else:
                bot.send_message(int(u_id), message.text or "", parse_mode="HTML")
            sent += 1
        except: failed += 1
        time.sleep(0.05)
    bot.send_message(admin_uid,
        f"📢 <b>ផ្សព្វផ្សាយរួចរាល់!</b>\n✅ បានផ្ញើ: {sent} | ❌ បរាជ័យ: {failed}",
        parse_mode="HTML", reply_markup=admin_kb())

# ═══════════════════════════════════════════════════════════
#  PHOTO HANDLER
# ═══════════════════════════════════════════════════════════
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    uid = message.chat.id
    step = waiting.get(uid)
    if uid == ADMIN_ID:
        # ── Premium Emoji flows also accept forwarded photos (caption emoji) ──
        if isinstance(step, dict) and step.get("step") == "await_setemoji_single":
            ch = step["char"]
            found = _extract_custom_emoji(message)
            if not found:
                bot.send_message(uid,
                    f"❌ រកមិនឃើញ premium emoji ក្នុងសារនោះទេ។ ផ្ញើ Premium version របស់ {ch} ម្តងទៀត ឬ ✕ Cancel។",
                    parse_mode="HTML", reply_markup=cancel_kb())
                return
            match_eid = next((eid for c, eid in found if c == ch), found[0][1])
            EMOJI_MAP[ch] = match_eid
            _save(EMOJI_FILE, EMOJI_MAP)
            waiting.pop(uid, None)
            remaining = [c for c, v in EMOJI_MAP.items() if not v]
            done_n = sum(1 for v in EMOJI_MAP.values() if v)
            if remaining:
                bot.send_message(uid,
                    f"✅ {ch} → <code>{match_eid}</code> កំណត់ជោគជ័យ!\n"
                    f"📊 {done_n}/{len(EMOJI_MAP)} — នៅសល់ {len(remaining)}\n\n"
                    f"👇 ជ្រើស emoji បន្ត:",
                    parse_mode="HTML", reply_markup=missing_emoji_kb())
            else:
                bot.send_message(uid,
                    f"✅ {ch} → <code>{match_eid}</code> កំណត់ជោគជ័យ!\n\n"
                    f"🎉 <b>រួចរាល់! Emoji ទាំងអស់បានកំណត់ 100%!</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
            return
        if step == "await_setemojis":
            report = _apply_setemojis(message)
            remaining = sum(1 for v in EMOJI_MAP.values() if not v)
            if not report:
                bot.send_message(uid,
                    "❌ រកមិនឃើញ premium/custom emoji ក្នុងសារនោះទេ។ ផ្ញើសារផ្សេងទៀត ឬ ✕ Cancel។",
                    parse_mode="HTML", reply_markup=cancel_kb())
                return
            if remaining == 0:
                waiting.pop(uid, None)
                bot.send_message(uid,
                    report + "\n\n🎉 <b>រួចរាល់! Emoji ទាំងអស់បានកំណត់ 100%!</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
            else:
                missing_preview = " ".join(ch for ch, v in EMOJI_MAP.items() if not v)[:200]
                bot.send_message(uid,
                    report + f"\n\n📤 ផ្ញើសារបន្តទៀត ({remaining} នៅសល់) ឬ ✕ Cancel ពេលរួច:\n⬜ {missing_preview}",
                    parse_mode="HTML", reply_markup=cancel_kb())
            return
        if step == "await_emojiid":
            report = _emojiid_text(message)
            if report:
                bot.send_message(uid, report + "\n\n📤 ផ្ញើសារបន្តទៀត ឬ ✕ Cancel ពេលរួច:",
                    parse_mode="HTML", reply_markup=cancel_kb())
            else:
                bot.send_message(uid,
                    "❌ រកមិនឃើញ premium/custom emoji ក្នុងសារនោះទេ។ ផ្ញើសារផ្សេងទៀត ឬ ✕ Cancel។",
                    parse_mode="HTML", reply_markup=cancel_kb())
            return
        if step == "broadcast_msg":
            _do_broadcast(uid, message)
        elif step == "set_welcome_photo":
            file_id = message.photo[-1].file_id
            _save_welcome_photo(file_id)
            waiting.pop(uid, None)
            bot.send_message(uid,
                "✅ <b>Welcome Photo បានរក្សា!</b>\n"
                "រូបនេះនឹងបង្ហាញពេល User ចុច /start",
                parse_mode="HTML", reply_markup=admin_kb())


# ═══════════════════════════════════════════════════════════
#  MAIN MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    uid     = message.chat.id
    uid_str = str(uid)
    text    = message.text or ""
    # ── Restore stripped-emoji text ──
    # បើ text នេះជា button ដែលមាន premium emoji icon (KeyboardButton.to_dict()
    # បានកាត់ emoji unicode ចេញពី label ដើម្បីកុំឲ្យស្ទួន icon), Telegram នឹង
    # ត្រឡប់តែ text ដែលកាត់រួច (គ្មាន emoji) មកវិញ។ ត្រូវ restore ទៅ text ដើម
    # (មាន emoji) វិញនៅទីនេះ មុននឹង logic ខាងក្រោម match text == / text in (...)
    # ណាមួយ — បើមិនធ្វើដូច្នេះទេ ប៊ូតុងទាំងអស់ដែលកំណត់ emoji premium នឹងធ្លាក់
    # ចូល fallback "មិនស្គាល់ button" រាល់ដង។
    text    = _STRIPPED_TEXT_MAP.get(text, text)
    lang    = get_lang(uid)
    step    = waiting.get(uid)

    _track_user(message)

    if is_banned(uid) and uid != ADMIN_ID:
        bot.send_message(uid, t(uid, "banned")); return

    # ── Cancel ──
    if text == "✕ Cancel":
        waiting.pop(uid, None)
        bot.send_message(uid, t(uid, "cancel_ok"),
                         reply_markup=main_kb(uid) if uid not in sub_admins and uid != ADMIN_ID
                         else (admin_kb() if uid == ADMIN_ID else sub_admin_kb()))
        return

    # ════════════════════════════════════════
    #  ADMIN SECTION
    # ════════════════════════════════════════
    if uid == ADMIN_ID or uid in sub_admins:
        _is_master_admin = (uid == ADMIN_ID)  # gate for master-only features

        # ── Premium Emoji button flow (replaces manual /setemojis, /emojiid) ──
        if isinstance(step, dict) and step.get("step") == "await_setemoji_single" and uid == ADMIN_ID:
            ch = step["char"]
            found = _extract_custom_emoji(message)
            if not found:
                bot.send_message(uid,
                    f"❌ រកមិនឃើញ premium emoji ក្នុងសារនោះទេ។ ផ្ញើ Premium version របស់ {ch} ម្តងទៀត ឬ ✕ Cancel។",
                    parse_mode="HTML", reply_markup=cancel_kb())
                return  # stay in loop, waiting untouched
            # prefer an exact match to the picked character; otherwise take the first found
            match_eid = next((eid for c, eid in found if c == ch), found[0][1])
            EMOJI_MAP[ch] = match_eid
            _save(EMOJI_FILE, EMOJI_MAP)
            waiting.pop(uid, None)
            remaining = [c for c, v in EMOJI_MAP.items() if not v]
            done_n = sum(1 for v in EMOJI_MAP.values() if v)
            if remaining:
                bot.send_message(uid,
                    f"✅ {ch} → <code>{match_eid}</code> កំណត់ជោគជ័យ!\n"
                    f"📊 {done_n}/{len(EMOJI_MAP)} — នៅសល់ {len(remaining)}\n\n"
                    f"👇 ជ្រើស emoji បន្ត:",
                    parse_mode="HTML", reply_markup=missing_emoji_kb())
            else:
                bot.send_message(uid,
                    f"✅ {ch} → <code>{match_eid}</code> កំណត់ជោគជ័យ!\n\n"
                    f"🎉 <b>រួចរាល់! Emoji ទាំងអស់បានកំណត់ 100%!</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
            return

        if step == "await_setemojis" and uid == ADMIN_ID:
            report = _apply_setemojis(message)
            remaining = sum(1 for v in EMOJI_MAP.values() if not v)
            if not report:
                bot.send_message(uid,
                    "❌ រកមិនឃើញ premium/custom emoji ក្នុងសារនោះទេ។ ផ្ញើសារផ្សេងទៀត ឬ ✕ Cancel។",
                    parse_mode="HTML", reply_markup=cancel_kb())
                return  # stay in loop, waiting untouched
            if remaining == 0:
                waiting.pop(uid, None)
                bot.send_message(uid,
                    report + "\n\n🎉 <b>រួចរាល់! Emoji ទាំងអស់បានកំណត់ 100%!</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
            else:
                # stay in the flow so admin can keep forwarding messages back-to-back
                missing_preview = " ".join(ch for ch, v in EMOJI_MAP.items() if not v)[:200]
                bot.send_message(uid,
                    report + f"\n\n📤 ផ្ញើសារបន្តទៀត ({remaining} នៅសល់) ឬ ✕ Cancel ពេលរួច:\n⬜ {missing_preview}",
                    parse_mode="HTML", reply_markup=cancel_kb())
            return

        if step == "await_emojiid" and uid == ADMIN_ID:
            report = _emojiid_text(message)
            if report:
                bot.send_message(uid, report + "\n\n📤 ផ្ញើសារបន្តទៀត ឬ ✕ Cancel ពេលរួច:",
                    parse_mode="HTML", reply_markup=cancel_kb())
            else:
                bot.send_message(uid,
                    "❌ រកមិនឃើញ premium/custom emoji ក្នុងសារនោះទេ។ ផ្ញើសារផ្សេងទៀត ឬ ✕ Cancel។",
                    parse_mode="HTML", reply_markup=cancel_kb())
            return  # stay in loop, waiting untouched

        # Admin commands
        if text.startswith("/addbal"):
            parts = text.split()
            if len(parts) < 3:
                bot.send_message(uid, "ប្រើ: /addbal UID AMOUNT"); return
            try:
                target = parts[1]; amt = float(parts[2])
                add_bal(int(target), amt)
                bot.send_message(uid,
                    f"✅ +${amt:.2f} → <code>{target}</code>\n💳 Balance: <b>${bal(int(target)):.2f}</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
                try: bot.send_message(int(target),
                    f"✅ Admin បន្ថែមលុយ! +${amt:.2f} | Balance: <b>${bal(int(target)):.2f}</b>",
                    parse_mode="HTML")
                except: pass
            except: bot.send_message(uid, "❌ Format ខុស")
            return

        if text.startswith("/deductbal"):
            parts = text.split()
            if len(parts) < 3:
                bot.send_message(uid, "ប្រើ: /deductbal UID AMOUNT"); return
            try:
                target = parts[1]; amt = float(parts[2])
                cur = bal(int(target))
                ded = min(amt, cur)
                ded_bal(int(target), ded)
                bot.send_message(uid,
                    f"✅ -${ded:.2f} → <code>{target}</code>\n💳 Balance: <b>${bal(int(target)):.2f}</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
            except: bot.send_message(uid, "❌ Format ខុស")
            return

        # ── /newbot — បង្កើត Bot ថ្មីដោយផ្ទាល់ខាងក្នុង Telegram (តែ master bot) ──
        if text == "/newbot":
            if not IS_MASTER:
                bot.send_message(uid, "🚫 Bot នេះជា bot រង — មិនអាចបង្កើត bot ថ្មីបានទេ។ សូមប្រើ bot ដើម។")
                return
            waiting[uid] = {"step": "newbot_name"}
            bot.send_message(uid,
                "🤖 <b>បង្កើត Bot ថ្មី</b>\n\n"
                "1️⃣ វាយឈ្មោះសម្គាល់ bot នេះ (អក្សរ/លេខ/_ តែប៉ុណ្ណោះ គ្មានគម្លាត)\n"
                "ឧ. <code>shop2</code>, <code>freefire_shop</code>\n\n✕ Cancel ដើម្បីបោះបង់",
                parse_mode="HTML", reply_markup=cancel_kb())
            return

        # ── /mybots — មើល/គ្រប់គ្រង bot ដែលបានបង្កើតទាំងអស់ (តែ master bot) ──
        if text == "/mybots":
            if not IS_MASTER:
                bot.send_message(uid, "🚫 Bot នេះជា bot រង — មិនមាន bot រងផ្សេងទេ។")
                return
            if not clone_registry:
                bot.send_message(uid, "📭 មិនទាន់មាន Bot រងណាមួយត្រូវបានបង្កើតទេ។ ប្រើ /newbot ដើម្បីបង្កើត។")
                return
            kb = InlineKeyboardMarkup(row_width=1)
            for nm in clone_registry:
                status = "🟢" if _clone_is_running(nm) else "🔴"
                kb.add(InlineKeyboardButton(f"{status} {nm}", callback_data=f"cln_view|{nm}", color="active" if _clone_is_running(nm) else "inactive"))
            bot.send_message(uid, "📋 <b>Bot រងទាំងអស់</b>\n🟢 = ដំណើរការ  🔴 = បិទ",
                              parse_mode="HTML", reply_markup=kb)
            return

        # ── Waiting steps for /newbot wizard ──
        if isinstance(step, dict) and step.get("step") == "newbot_name":
            safe = "".join(ch for ch in text.strip() if (ch.isascii() and ch.isalnum()) or ch == "_")
            if not safe:
                bot.send_message(uid, "⚠️ ឈ្មោះមិនត្រឹមត្រូវ សូមវាយម្តងទៀត:", reply_markup=cancel_kb()); return
            if safe in clone_registry:
                bot.send_message(uid, "⚠️ ឈ្មោះនេះមានរួចហើយ សូមប្រើឈ្មោះផ្សេង:", reply_markup=cancel_kb()); return
            waiting[uid] = {"step": "newbot_token", "name": safe}
            bot.send_message(uid, "2️⃣ វាយ <b>Bot Token</b> (ពី @BotFather):",
                              parse_mode="HTML", reply_markup=cancel_kb())
            return

        if isinstance(step, dict) and step.get("step") == "newbot_token":
            tok = text.strip()
            if ":" not in tok or len(tok) < 20:
                bot.send_message(uid, "⚠️ Token មិនត្រឹមត្រូវ សូមផ្ញើម្តងទៀត:", reply_markup=cancel_kb()); return
            waiting[uid] = {**step, "step": "newbot_admin", "token": tok}
            bot.send_message(uid, "3️⃣ វាយ <b>Admin Telegram ID</b> របស់អ្នកគ្រប់គ្រង bot នេះ (លេខ):",
                              parse_mode="HTML", reply_markup=cancel_kb())
            return

        if isinstance(step, dict) and step.get("step") == "newbot_admin":
            if not text.strip().isdigit():
                bot.send_message(uid, "⚠️ សូមផ្ញើជាលេខតែប៉ុណ្ណោះ:", reply_markup=cancel_kb()); return
            waiting[uid] = {**step, "step": "newbot_key", "new_admin_id": int(text.strip())}
            bot.send_message(uid, "4️⃣ វាយ <b>CamRapidPay API Key</b> សម្រាប់ bot នេះ:",
                              parse_mode="HTML", reply_markup=cancel_kb())
            return

        if isinstance(step, dict) and step.get("step") == "newbot_key":
            key = text.strip()
            if len(key) < 10:
                bot.send_message(uid, "⚠️ API Key ខ្លីពេក សូមផ្ញើម្តងទៀត:", reply_markup=cancel_kb()); return
            name = step["name"]; tok = step["token"]; new_admin = step["new_admin_id"]
            port = _next_clone_port()
            masked_tok = tok[:10] + "..." + tok[-4:]
            masked_key = key[:6] + "..." + key[-4:]
            waiting[uid] = {**step, "step": "newbot_display", "camrapid_key": key, "port": port}
            bot.send_message(uid,
                "5️⃣ វាយ <b>ឈ្មោះ bot</b> ដែលបង្ហាញដល់អ្នកប្រើ (ឧ. <code>Jak Like Shop</code>)\n"
                "ឬផ្ញើ <code>-</code> ដើម្បីប្រើឈ្មោះ internal (<code>"
                + step["name"] + "</code>) ជំនួស:",
                parse_mode="HTML", reply_markup=cancel_kb())
            return

        if isinstance(step, dict) and step.get("step") == "newbot_display":
            raw = text.strip()
            display = step["name"] if raw == "-" else raw[:60]
            waiting[uid] = {**step, "step": "newbot_welcome", "display_name": display}
            bot.send_message(uid,
                "6️⃣ វាយ <b>Welcome Message</b> custom សម្រាប់ bot នេះ\n"
                "ប្រើ <code>{}</code> ដើម្បីដាក់ balance ក្នុង text\n"
                "ឬផ្ញើ <code>-</code> ដើម្បីប្រើ welcome message default:",
                parse_mode="HTML", reply_markup=cancel_kb())
            return

        if isinstance(step, dict) and step.get("step") == "newbot_welcome":
            raw = text.strip()
            welcome = "" if raw == "-" else raw
            name = step["name"]; tok = step["token"]; new_admin = step["new_admin_id"]
            port = step["port"]; display = step["display_name"]
            masked_tok = tok[:10] + "..." + tok[-4:]
            masked_key = step["camrapid_key"][:6] + "..." + step["camrapid_key"][-4:]
            waiting[uid] = {**step, "step": "newbot_confirm", "welcome_msg": welcome}
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ បង្កើត ហើយ ដំណើរការ", callback_data="newbot_confirm_yes", color="active"))
            kb.add(InlineKeyboardButton("❌ បោះបង់", callback_data="newbot_confirm_no", color="inactive"))
            bot.send_message(uid,
                f"📋 <b>ត្រួតពិនិត្យ</b>\n\n"
                f"ឈ្មោះ internal: <code>{name}</code>\n"
                f"ឈ្មោះ display: <code>{display}</code>\n"
                f"Token: <code>{masked_tok}</code>\n"
                f"Admin ID: <code>{new_admin}</code>\n"
                f"CamRapidPay Key: <code>{masked_key}</code>\n"
                f"Welcome: <code>{'(default)' if not welcome else welcome[:80]}</code>\n\n"
                f"ត្រឹមត្រូវទេ?",
                parse_mode="HTML", reply_markup=kb)
            return

        # ── Waiting steps ──
        if isinstance(step, dict) and step.get("step") == "add_balance_amt":
            target = step["target"]
            try:
                amt = float(text.replace("$",""))
                add_bal(int(target), amt)
                _save(WALLETS_FILE, wallets)
                waiting.pop(uid, None)
                bot.send_message(uid,
                    f"✅ <b>បន្ថែម Balance</b>\n👤 <code>{target}</code>\n"
                    f"💰 +${amt:.2f} | Balance: <b>${bal(int(target)):.2f}</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
                try: bot.send_message(int(target),
                    f"✅ <b>Admin បន្ថែមលុយ!</b>\n💰 +${amt:.2f} | Balance: <b>${bal(int(target)):.2f}</b>",
                    parse_mode="HTML")
                except: pass
            except: bot.send_message(uid, "❌ Amount ខុស! ឧ: <code>5.00</code>", parse_mode="HTML")
            return

        if isinstance(step, dict) and step.get("step") == "deduct_balance_amt":
            target = step["target"]
            try:
                amt  = float(text.replace("$",""))
                cur  = bal(int(target))
                ded  = min(amt, cur)
                ded_bal(int(target), ded)
                waiting.pop(uid, None)
                bot.send_message(uid,
                    f"✅ <b>កាត់ Balance</b>\n👤 <code>{target}</code>\n"
                    f"💔 -${ded:.2f} | Balance: <b>${bal(int(target)):.2f}</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
                try: bot.send_message(int(target),
                    f"⚠️ <b>Admin កាត់លុយ!</b>\n💔 -${ded:.2f} | Balance: <b>${bal(int(target)):.2f}</b>",
                    parse_mode="HTML")
                except: pass
            except: bot.send_message(uid, "❌ Amount ខុស!")
            return

        if isinstance(step, dict) and step.get("step") == "edit_svc_name":
            slug = step.get("slug")
            s    = smm_services.get(slug)
            if not s:
                bot.send_message(uid, "❌ Service រកមិនឃើញ", reply_markup=admin_kb())
                waiting.pop(uid, None); return
            old_label = s.get("label", slug)
            new_label = text.strip()
            if not new_label:
                bot.send_message(uid, "❌ ឈ្មោះទទេ! សូមវាយម្តងទៀត"); return
            smm_services[slug]["label"] = new_label
            _save(SMM_SVC_FILE, smm_services)
            waiting.pop(uid, None)
            bot.send_message(uid,
                f"✅ <b>ឈ្មោះ Service បានផ្លាស់ប្តូរ!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 API ID: <code>{s.get('api_id','?')}</code>\n"
                f"📝 ចាស់: <s>{old_label}</s>\n"
                f"✨ ថ្មី: <b>{new_label}</b>",
                parse_mode="HTML", reply_markup=admin_kb())
            return

        if step == "promo_add_code":
            parts = text.strip().split()
            if len(parts) < 4:
                bot.send_message(uid,
                    "❌ Format ខុស!\nឧ: <code>SAVE50 50 pct 100</code>\n"
                    "ឬ: <code>GIFT1 1.00 fix 50</code>", parse_mode="HTML"); return
            code = parts[0].upper()
            try:
                discount = float(parts[1])
                pct  = (parts[2].lower() == "pct")
                uses = int(parts[3])
            except:
                bot.send_message(uid, "❌ Format ខុស!", parse_mode="HTML"); return
            promos[code] = {"discount": discount, "pct": pct, "uses": uses, "used": 0}
            _save(PROMO_FILE, promos)
            waiting.pop(uid, None)
            dtype = f"{discount:.0f}%" if pct else f"${discount:.2f}"
            bot.send_message(uid,
                f"✅ <b>Promo Code Created!</b>\n"
                f"🎟️ <code>{code}</code> — <b>{dtype}</b> | {uses} uses",
                parse_mode="HTML", reply_markup=admin_kb()); return

        if step == "broadcast_msg":
            _do_broadcast(uid, message); return

        if step == "smm_add_cat":
            waiting[uid] = {"step": "smm_add_ids", "cat": text}
            bot.send_message(uid,
                f"📂 Category: <b>{text}</b>\n"
                f"ផ្ញើ API Service IDs (comma):\n"
                f"ឧ: <code>5441,5448,5502</code>\n\n"
                f"💡 រក IDs នៅ SMM API Panel ➡️ Services",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if isinstance(step, dict) and step.get("step") == "smm_add_ids":
            cat = step["cat"]
            # Check API configured first
            if not smm_api.get("url") or not smm_api.get("key"):
                waiting.pop(uid, None)
                bot.send_message(uid,
                    "❌ <b>SMM API មិនទាន់ Set!</b>\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "ចុច <b>🔗 Set SMM API</b> ជាមុន រួចទើបបន្ថែម Service",
                    parse_mode="HTML", reply_markup=admin_kb()); return
            ids = [i.strip() for i in text.replace(" ", "").split(",") if i.strip().isdigit()]
            if not ids:
                bot.send_message(uid, "❌ ផ្ញើ IDs ជាលេខ ឧ: <code>5441,5448</code>",
                                 parse_mode="HTML"); return
            bot.send_message(uid, f"⏳ Fetching {len(ids)} service(s) from API...")
            ok, fail = [], []
            for api_id in ids:
                info = _smm_fetch_service(api_id)
                if info:
                    slug = f"{cat.lower().replace(' ', '_')}_{api_id}"
                    smm_services[slug] = {
                        "api_id":    api_id,
                        "cost_rate": info["cost_rate"],
                        "min":       info["min"],
                        "max":       info["max"],
                        "label":     _smm_clean_name(info["raw_name"]),
                        "category":  cat,
                    }
                    ok.append(f"✅ <code>{api_id}</code> — {smm_services[slug]['label']}")
                else:
                    fail.append(f"❌ <code>{api_id}</code> — not found / API error")
            if ok:
                _save(SMM_SVC_FILE, smm_services)
            waiting.pop(uid, None)
            msg = f"<b>📊 SMM Import — {cat}</b>\n━━━━━━━━━━━━━━━━━━\n" + "\n".join(ok)
            if fail: msg += "\n\n<b>Failed:</b>\n" + "\n".join(fail)
            msg += f"\n\n✅ Total services: <b>{len(smm_services)}</b>"
            bot.send_message(uid, msg, parse_mode="HTML", reply_markup=admin_kb()); return

        if step == "smm_api_url":
            smm_api["url"] = text.strip().rstrip("/")
            waiting[uid] = "smm_api_key"
            bot.send_message(uid,
                f"✅ URL: <code>{smm_api['url']}</code>\n\n🔑 ឥឡូវ ផ្ញើ API Key:",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if step == "smm_api_key":
            smm_api["key"] = text.strip()
            _save(SMM_API_FILE, smm_api)
            waiting.pop(uid, None)
            bot.send_message(uid, "⏳ Testing connection...", reply_markup=admin_kb())
            try:
                r = http.post(smm_api["url"],
                              data={"key": smm_api["key"], "action": "balance"}, timeout=10)
                d = r.json()
                balance  = d.get("balance", d.get("Balance", "?"))
                currency = d.get("currency", d.get("Currency", "USD"))
                bot.send_message(uid,
                    f"✅ <b>SMM API ភ្ជាប់ហើយ!</b>\n━━━━━━━━━━━━━━━━━━\n"
                    f"🌐 URL: <code>{smm_api['url']}</code>\n"
                    f"💰 Balance: <b>{balance} {currency}</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
            except Exception as e:
                bot.send_message(uid,
                    f"⚠️ API Saved ប៉ុន្តែ test failed: <code>{e}</code>",
                    parse_mode="HTML", reply_markup=admin_kb())
            return

        if isinstance(step, dict) and step.get("step") == "depbonus_edit":
            try:
                parts = [p.strip() for p in text.replace("$", "").split(",")]
                if len(parts) != 2:
                    raise ValueError
                min_amt = float(parts[0]); pct = float(parts[1])
                if min_amt < 0 or pct < 0:
                    raise ValueError
                dep_bonus_cfg["min_amount"] = min_amt
                dep_bonus_cfg["pct"] = pct
                _save(DEP_BONUS_FILE, dep_bonus_cfg)
                waiting.pop(uid, None)
                bot.send_message(uid, f"✅ បានកែ!\n{_dep_bonus_status_text()}",
                                 parse_mode="HTML", reply_markup=admin_kb())
            except Exception:
                bot.send_message(uid,
                    "❌ ទម្រង់ខុស! សូមផ្ញើជា <code>ចំនួនអប្បបរមា,ភាគរយ</code>\nឧ: <code>1,5</code> (ដាក់ $1 ឡើងទៅ ទទួល 5%)",
                    parse_mode="HTML", reply_markup=cancel_kb())
            return

        if isinstance(step, dict) and step.get("step") == "smm_set_profit":
            try:
                pct = float(text)
                smm_profit["pct"] = pct; _save(SMM_PROFIT_FILE, smm_profit)
                waiting.pop(uid, None)
                bot.send_message(uid, f"✅ SMM Profit <b>{pct:.0f}%</b>",
                                 parse_mode="HTML", reply_markup=admin_kb())
            except: bot.send_message(uid, "❌ ត្រូវជាលេខ")
            return

        # ── Manual service: step 1 label ──
        if isinstance(step, dict) and step.get("step") == "manual_svc_label":
            label = text.strip()
            if not label:
                bot.send_message(uid, "❌ ឈ្មោះទទេ! វាយម្តងទៀត:", reply_markup=cancel_kb()); return
            waiting[uid] = {"step": "manual_svc_cat", "label": label}
            cats_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 TikTok",    callback_data="mansvc_cat:TikTok", color="active"),
                 InlineKeyboardButton("📘 Facebook",  callback_data="mansvc_cat:Facebook", color="active")],
                [InlineKeyboardButton("📸 Instagram", callback_data="mansvc_cat:Instagram", color="active"),
                 InlineKeyboardButton("▶️ YouTube",   callback_data="mansvc_cat:YouTube", color="active")],
                [InlineKeyboardButton("📱 Telegram",  callback_data="mansvc_cat:Telegram", color="active"),
                 InlineKeyboardButton("🐦 Twitter",   callback_data="mansvc_cat:Twitter", color="active")],
                [InlineKeyboardButton("✏️ ផ្សេង (Custom)", callback_data="mansvc_cat:__custom__", color="progress")],
            ])
            bot.send_message(uid,
                f"📂 <b>ជ្រើស Category</b>\n"
                f"📝 ឈ្មោះ: <b>{label}</b>",
                parse_mode="HTML", reply_markup=cats_kb); return

        if isinstance(step, dict) and step.get("step") == "manual_svc_cat_custom":
            cat = text.strip()
            if not cat:
                bot.send_message(uid, "❌ Category ទទេ!", reply_markup=cancel_kb()); return
            waiting[uid] = {"step": "manual_svc_price", "label": step["label"], "cat": cat}
            bot.send_message(uid,
                f"💰 <b>ដាក់តម្លៃ (USD per 1000)</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"ឧ: <code>0.50</code> = $0.50 per 1K\n"
                f"ឧ: <code>1.20</code> = $1.20 per 1K",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if isinstance(step, dict) and step.get("step") == "manual_svc_price":
            try:
                price = float(text.replace("$","").strip())
                if price <= 0: raise ValueError
            except:
                bot.send_message(uid, "❌ តម្លៃខុស! ឧ: <code>0.50</code>",
                                 parse_mode="HTML", reply_markup=cancel_kb()); return
            waiting[uid] = {**step, "step": "manual_svc_min", "price": price}
            bot.send_message(uid,
                f"🔢 <b>Min Order</b> (ចំនួនអប្បបរមា)\n"
                f"ឧ: <code>100</code>",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if isinstance(step, dict) and step.get("step") == "manual_svc_min":
            try:
                mn = int(text.strip())
                if mn <= 0: raise ValueError
            except:
                bot.send_message(uid, "❌ ត្រូវជាលេខ! ឧ: <code>100</code>",
                                 parse_mode="HTML", reply_markup=cancel_kb()); return
            waiting[uid] = {**step, "step": "manual_svc_max", "min": mn}
            bot.send_message(uid,
                f"🔢 <b>Max Order</b> (ចំនួនអតិបរមា)\n"
                f"ឧ: <code>50000</code>",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if isinstance(step, dict) and step.get("step") == "manual_svc_max":
            try:
                mx = int(text.strip())
                if mx <= 0: raise ValueError
            except:
                bot.send_message(uid, "❌ ត្រូវជាលេខ! ឧ: <code>50000</code>",
                                 parse_mode="HTML", reply_markup=cancel_kb()); return
            # Save manual service
            label = step["label"]; cat = step["cat"]; price = step["price"]; mn = step["min"]
            slug  = f"manual_{cat.lower().replace(' ','_')}_{int(time.time())}"
            smm_services[slug] = {
                "api_id":       None,          # No API — manual
                "manual":       True,
                "cost_rate":    price,
                "min":          mn,
                "max":          mx,
                "label":        label,
                "category":     cat,
            }
            _save(SMM_SVC_FILE, smm_services)
            waiting.pop(uid, None)
            bot.send_message(uid,
                f"✅ <b>Manual Service បានបន្ថែម!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📝 ឈ្មោះ: <b>{label}</b>\n"
                f"📂 Category: <b>{cat}</b>\n"
                f"💰 តម្លៃ: <b>${price:.2f}/1K</b>\n"
                f"🔢 Min: <b>{mn:,}</b> · Max: <b>{mx:,}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✍️ <i>Service នេះ Admin ត្រូវ process ដោយដៃ</i>",
                parse_mode="HTML", reply_markup=admin_kb()); return

        # ── Admin: Update manual order status ──
        if isinstance(step, dict) and step.get("step") == "manual_order_done" and uid == ADMIN_ID:
            oid      = step.get("oid")
            user_uid = step.get("user_uid")
            o        = smm_orders.get(oid)
            if not o:
                bot.send_message(uid, "❌ Order រកមិនឃើញ", reply_markup=admin_kb())
                waiting.pop(uid, None); return
            note = text.strip()
            smm_orders[oid]["status"]   = "completed"
            smm_orders[oid]["note"]     = note
            _save(SMM_ORD_FILE, smm_orders)
            waiting.pop(uid, None)
            try:
                bot.send_message(int(user_uid),
                    f"✅ <b>Order បានដំណើរការហើយ!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 <code>{oid}</code>\n"
                    f"📊 {o.get('label','?')}\n"
                    f"🔢 ចំនួន: <b>{o.get('qty',0):,}</b>\n"
                    + (f"📝 Note: {note}\n" if note and note != "-" else "") +
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🙏 អរគុណ!",
                    parse_mode="HTML")
            except: pass
            bot.send_message(uid,
                f"✅ <b>Order Completed!</b>\n🆔 <code>{oid}</code>",
                parse_mode="HTML", reply_markup=admin_kb()); return

        if text == "✍️ Manual SMM":
            waiting[uid] = {"step": "manual_svc_label"}
            bot.send_message(uid,
                "✍️ <b>បន្ថែម Manual Service</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<i>Service ប្រភេទនេះ Admin process ដោយដៃ\n"
                "ប្រើសម្រាប់: TikTok Khmer, Reseller, ល.ល</i>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "📝 <b>វាយ ឈ្មោះ Service:</b>\n"
                "ឧ: <code>TikTok Likes Khmer</code>",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        # ── Package (flat-price bundle): step 1 label ──
        if text == "📦 បន្ថែម Package":
            waiting[uid] = {"step": "pkg_label"}
            bot.send_message(uid,
                "📦 <b>បន្ថែម Package ថ្មី (កញ្ចប់តម្លៃថេរ)</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<i>ប្រើសម្រាប់កញ្ចប់ Like+View+Follow ដូច TikTok Khmer\n"
                "(តម្លៃថេរក្នុងមួយ Order — មិនគិតតាម 1K ទេ)</i>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "📝 <b>វាយ ឈ្មោះ Package:</b>\n"
                "ឧ: <code>1K-2K Like + 3.5K View</code>",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if isinstance(step, dict) and step.get("step") == "pkg_label":
            label = text.strip()
            if not label:
                bot.send_message(uid, "❌ ឈ្មោះទទេ! វាយម្តងទៀត:", reply_markup=cancel_kb()); return
            waiting[uid] = {"step": "pkg_cat", "label": label}
            cats_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🇰🇭 TikTok Khmer", callback_data="pkgcat:🇰🇭 TikTok Khmer", color="active")],
                [InlineKeyboardButton("🎵 TikTok",    callback_data="pkgcat:TikTok", color="active"),
                 InlineKeyboardButton("📘 Facebook",  callback_data="pkgcat:Facebook", color="active")],
                [InlineKeyboardButton("📸 Instagram", callback_data="pkgcat:Instagram", color="active"),
                 InlineKeyboardButton("▶️ YouTube",   callback_data="pkgcat:YouTube", color="active")],
                [InlineKeyboardButton("✏️ ផ្សេង (Custom)", callback_data="pkgcat:__custom__", color="progress")],
            ])
            bot.send_message(uid,
                f"📂 <b>ជ្រើស Category</b>\n📝 ឈ្មោះ: <b>{label}</b>",
                parse_mode="HTML", reply_markup=cats_kb); return

        if isinstance(step, dict) and step.get("step") == "pkg_cat_custom":
            cat = text.strip()
            if not cat:
                bot.send_message(uid, "❌ Category ទទេ!", reply_markup=cancel_kb()); return
            waiting[uid] = {"step": "pkg_desc", "label": step["label"], "cat": cat}
            bot.send_message(uid,
                "📝 <b>ការពិពណ៌នា Package (Description)</b>\n"
                "ឧ: <code>1K-2K Likes ❤️ + 3.5K Views 👁</code>\n"
                "ឬ វាយ <code>-</code> ដើម្បីរំលង",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if isinstance(step, dict) and step.get("step") == "pkg_desc":
            desc = text.strip()
            waiting[uid] = {**step, "step": "pkg_price", "desc": ("" if desc == "-" else desc)}
            bot.send_message(uid,
                "💰 <b>ដាក់តម្លៃ Package (USD / កញ្ចប់)</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "ឧ: <code>0.99</code> = $0.99 ក្នុងមួយកញ្ចប់",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if isinstance(step, dict) and step.get("step") == "pkg_price":
            try:
                price = float(text.replace("$","").strip())
                if price <= 0: raise ValueError
            except:
                bot.send_message(uid, "❌ តម្លៃខុស! ឧ: <code>0.99</code>",
                                 parse_mode="HTML", reply_markup=cancel_kb()); return
            label = step["label"]; cat = step["cat"]; desc = step.get("desc", "")
            slug = f"manual_pkg_{cat.lower().replace(' ','_')}_{int(time.time())}"
            smm_services[slug] = {
                "api_id":      None,
                "manual":      True,
                "cost_rate":   0,
                "min":         1,
                "max":         1,
                "label":       label,
                "category":    cat,
                "flat_price":  price,
                "preset_qtys": [1],
                "description": desc,
            }
            _save(SMM_SVC_FILE, smm_services)
            waiting.pop(uid, None)
            bot.send_message(uid,
                f"✅ <b>Package បានបន្ថែម!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📝 ឈ្មោះ: <b>{label}</b>\n"
                f"📂 Category: <b>{cat}</b>\n"
                f"💰 តម្លៃ: <b>${price:.2f}/order</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✍️ <i>Package នេះ Admin ត្រូវ process ដោយដៃ</i>",
                parse_mode="HTML", reply_markup=admin_kb()); return

        # ── Edit price of an existing service/package ──
        if text == "💰 កែតម្លៃ":
            if not smm_services:
                bot.send_message(uid, "❌ គ្មាន SMM Service ទេ", reply_markup=admin_kb()); return
            cats = {}
            for slug, s in smm_services.items():
                cat = s.get("category", "Other")
                cats.setdefault(cat, []).append((slug, s))
            for cat, svcs in cats.items():
                btns = []
                for slug, s in svcs:
                    label = s.get("label", slug)[:28]
                    if s.get("flat_price"):
                        price_txt = f"${float(s['flat_price']):.2f}"
                    else:
                        price_txt = f"${float(s.get('cost_rate',0)):.2f}/1K"
                    btns.append([InlineKeyboardButton(
                        f"💰 {label} ({price_txt})", callback_data=f"editprice:{slug}", color="progress")])
                bot.send_message(uid,
                    f"💰 <b>កែតម្លៃ — {cat}</b>\n━━━━━━━━━━━━━━━━━━\nចុចដើម្បីកែតម្លៃ:",
                    parse_mode="HTML", reply_markup=InlineKeyboardMarkup(btns))
            return

        if isinstance(step, dict) and step.get("step") == "edit_svc_price":
            slug = step.get("slug")
            s    = smm_services.get(slug)
            if not s:
                bot.send_message(uid, "❌ Service រកមិនឃើញ", reply_markup=admin_kb())
                waiting.pop(uid, None); return
            try:
                new_price = float(text.replace("$","").strip())
                if new_price <= 0: raise ValueError
            except:
                bot.send_message(uid, "❌ តម្លៃខុស! ឧ: <code>1.99</code>",
                                 parse_mode="HTML", reply_markup=cancel_kb()); return
            is_flat = bool(s.get("flat_price"))
            if is_flat:
                old_price = float(s.get("flat_price", 0))
                smm_services[slug]["flat_price"] = new_price
                unit = "/order"
            else:
                old_price = float(s.get("cost_rate", 0))
                smm_services[slug]["cost_rate"] = new_price
                unit = "/1K"
            _save(SMM_SVC_FILE, smm_services)
            waiting.pop(uid, None)
            bot.send_message(uid,
                f"✅ <b>តម្លៃបានផ្លាស់ប្តូរ!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📝 {s.get('label', slug)}\n"
                f"💰 ចាស់: <s>${old_price:.2f}{unit}</s>\n"
                f"✨ ថ្មី: <b>${new_price:.2f}{unit}</b>",
                parse_mode="HTML", reply_markup=admin_kb())
            return

        if text == "📊 ការបញ្ជា SMM":
            if not smm_orders:
                bot.send_message(uid, "❌ គ្មានការបញ្ជា SMM", reply_markup=admin_kb()); return
            lines = ["<b>📊 ការបញ្ជា SMM (20 ចុងក្រោយ)</b>\n━━━━━━━━━━━━━━━━━━"]
            for oid, o in list(smm_orders.items())[-20:]:
                lines.append(f"🆔 <code>{oid}</code> | 👤 <code>{o['uid']}</code>\n  {o.get('label','?')} | Qty:{o.get('qty','?')} | ${o.get('price',0):.4f} | {o.get('status','?')}")
            bot.send_message(uid, "\n".join(lines)[:4000], parse_mode="HTML", reply_markup=admin_kb()); return

        if text == "⚙️ កំណត់ SMM API":
            cur_url = smm_api.get("url","❌ មិនទាន់ set")
            cur_key = smm_api.get("key","❌ មិនទាន់ set")
            masked = cur_key[:6] + "****" + cur_key[-4:] if len(cur_key) > 10 else cur_key
            kb_api = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ កំណត់ URL + Key", callback_data="smmapi:setup", color="progress")],
                [InlineKeyboardButton("🔌 សាកល្បងភ្ជាប់",  callback_data="smmapi:test", color="active")],
                [InlineKeyboardButton("🗑️ លុប API",         callback_data="smmapi:clear", color="inactive")],
            ])
            bot.send_message(uid,
                f"⚙️ <b>SMM API Config</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"🌐 URL: <code>{cur_url}</code>\n"
                f"🔑 Key: <code>{masked}</code>",
                parse_mode="HTML", reply_markup=kb_api); return

        if text == "➕ បន្ថែម SMM":
            cats_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 TikTok",    callback_data="smmaddcat:TikTok", color="active"),
                 InlineKeyboardButton("📘 Facebook",  callback_data="smmaddcat:Facebook", color="active")],
                [InlineKeyboardButton("📸 Instagram", callback_data="smmaddcat:Instagram", color="active"),
                 InlineKeyboardButton("▶️ YouTube",   callback_data="smmaddcat:YouTube", color="active")],
                [InlineKeyboardButton("📱 Telegram",  callback_data="smmaddcat:Telegram", color="active"),
                 InlineKeyboardButton("🐦 Twitter",   callback_data="smmaddcat:Twitter", color="active")],
                [InlineKeyboardButton("✏️ Custom Category", callback_data="smmaddcat:custom", color="progress")],
            ])
            bot.send_message(uid,
                "➕ <b>បន្ថែម SMM Service</b>\n━━━━━━━━━━━━━━━━━━\nជ្រើស Category:",
                parse_mode="HTML", reply_markup=cats_kb); return

        if text == "🗑️ លុប SMM":
            if not smm_services:
                bot.send_message(uid, "❌ គ្មាន SMM Service ទេ", reply_markup=admin_kb()); return
            cats = {}
            for slug, s in smm_services.items():
                cat = s.get("category", "Other")
                cats.setdefault(cat, []).append((slug, s))
            for cat, svcs in cats.items():
                btns = []
                for slug, s in svcs:
                    label = s.get("label", slug)[:30]
                    api_id = s.get("api_id", "?")
                    btns.append([InlineKeyboardButton(
                        f"🗑️ [{api_id}] {label}", callback_data=f"delsvc:{slug}", color="inactive")])
                btns.append([InlineKeyboardButton(
                    f"🗑️ លុបទាំងអស់ {cat}", callback_data=f"delsvc:cat:{cat}", color="inactive")])
                bot.send_message(uid,
                    f"📂 <b>{cat}</b> — {len(svcs)} services\n━━━━━━━━━━━━━━━━━━",
                    parse_mode="HTML", reply_markup=InlineKeyboardMarkup(btns))
            return

        if text == "✏️ កែ SMM":
            if not smm_services:
                bot.send_message(uid, "❌ គ្មាន SMM Service ទេ", reply_markup=admin_kb()); return
            cats = {}
            for slug, s in smm_services.items():
                cat = s.get("category", "Other")
                cats.setdefault(cat, []).append((slug, s))
            for cat, svcs in cats.items():
                btns = []
                for slug, s in svcs:
                    label  = s.get("label", slug)[:35]
                    api_id = s.get("api_id", "?")
                    btns.append([InlineKeyboardButton(
                        f"✏️ [{api_id}] {label}", callback_data=f"editsvc:{slug}", color="progress")])
                bot.send_message(uid,
                    f"✏️ <b>កែឈ្មោះ — {cat}</b>\n━━━━━━━━━━━━━━━━━━\nចុចដើម្បីកែ:",
                    parse_mode="HTML", reply_markup=InlineKeyboardMarkup(btns))
            return

        if text == "📋 SMM Services":
            bot.send_message(uid, _smm_service_list_text(), parse_mode="HTML", reply_markup=admin_kb()); return

        if text == "💹 ប្រាក់ចំណេញ SMM":
            waiting[uid] = {"step": "smm_set_profit"}
            bot.send_message(uid,
                f"💹 <b>ប្រាក់ចំណេញ SMM: {_smm_profit_pct():.0f}%</b>\nផ្ញើ % ថ្មី:",
                parse_mode="HTML", reply_markup=cancel_kb()); return

        if text == "🎁 Bonus ដាក់លុយ":
            btns = InlineKeyboardMarkup()
            toggle_label = "🔴 បិទ Auto Bonus" if dep_bonus_cfg.get("enabled", True) else "🟢 បើក Auto Bonus"
            btns.add(InlineKeyboardButton(toggle_label, callback_data="depbonus:toggle",
                                          color=("danger" if dep_bonus_cfg.get("enabled", True) else "active")))
            btns.add(InlineKeyboardButton("✏️ កែ % / ចំនួនអប្បបរមា", callback_data="depbonus:edit", color="progress"))
            bot.send_message(uid,
                f"{_dep_bonus_status_text()}\n━━━━━━━━━━━━━━━━━━\n"
                f"👉 អ្នកប្រើដាក់លុយចាប់ពី <b>${float(dep_bonus_cfg.get('min_amount',1.0)):.2f}</b> ឡើងទៅ "
                f"នឹងទទួល Bonus <b>{float(dep_bonus_cfg.get('pct',5.0)):.0f}%</b> បញ្ចូល Balance ដោយស្វ័យប្រវត្តិ "
                f"(បូកបន្ថែមលើ Promo Code ប្រសិនបើមាន)។",
                parse_mode="HTML", reply_markup=btns); return

        if text == "💰 ឆែកលុយ API":
            url = smm_api.get("url",""); key = smm_api.get("key","")
            if not url or not key:
                bot.send_message(uid, "❌ SMM API មិនទាន់ set!", reply_markup=admin_kb()); return
            try:
                r = http.post(url, data={"key": key, "action": "balance"}, timeout=10)
                d = r.json()
                balance  = d.get("balance", d.get("Balance", "?"))
                currency = d.get("currency", d.get("Currency", "USD"))
                bot.send_message(uid,
                    f"💰 <b>SMM API Balance</b>\n━━━━━━━━━━━━━━━━━━\n"
                    f"💵 Balance: <b>{balance} {currency}</b>\n"
                    f"🌐 API: <code>{url}</code>",
                    parse_mode="HTML", reply_markup=admin_kb())
            except Exception as e:
                bot.send_message(uid, f"❌ API Error: {e}", reply_markup=admin_kb())
            return

        if text == "💰 កាបូបលុយ":
            lines = ["<b>💰 កាបូបលុយអ្នកប្រើ</b>\n━━━━━━━━━━━━━━━━━━"]
            for u_id, u_info in sorted(users_db.items(), key=lambda x: x[1].get("last",0), reverse=True)[:30]:
                b = wallets.get(u_id, 0)
                name = u_info.get("name","?")
                lines.append(f"👤 <b>{name}</b> <code>{u_id}</code> — <b>${float(b):.2f}</b>")
            bot.send_message(uid, "\n".join(lines)[:4000], parse_mode="HTML", reply_markup=admin_kb()); return

        if text == "💳 ប្រាក់បញ្ញើ":
            pend = [(k, v) for k, v in smm_deps.items() if v.get("status")=="pending"]
            if not pend:
                bot.send_message(uid, "✅ គ្មាន pending deposit", reply_markup=admin_kb()); return
            lines = ["<b>💳 ប្រាក់បញ្ញើ រង់ចាំ</b>\n━━━━━━━━━━━━━━━━━━"]
            for k, v in pend:
                lines.append(f"👤 <code>{v.get('uid','?')}</code> | ${v.get('amount',0):.2f}")
            bot.send_message(uid, "\n".join(lines)[:4000], parse_mode="HTML", reply_markup=admin_kb()); return

        if text == "💸 បន្ថែមប្រាក់":
            users_sorted = sorted(users_db.items(), key=lambda x: x[1].get("last",0), reverse=True)[:15]
            btns = []
            for u_id, u_info in users_sorted:
                b    = float(wallets.get(u_id, 0))
                name = (u_info.get("name") or "?")[:18]
                btns.append([InlineKeyboardButton(
                    f"👤 {name}  ${b:.2f}", callback_data=f"useraction:addbal:{u_id}", color="active")])
            bot.send_message(uid,
                "💸 <b>បន្ថែមប្រាក់</b>\n━━━━━━━━━━━━━━━━━━\nជ្រើសអ្នកប្រើ:",
                parse_mode="HTML", reply_markup=InlineKeyboardMarkup(btns)); return

        if text == "💔 កាត់ប្រាក់":
            users_sorted = sorted(users_db.items(), key=lambda x: x[1].get("last",0), reverse=True)[:15]
            btns = []
            for u_id, u_info in users_sorted:
                b    = float(wallets.get(u_id, 0))
                name = (u_info.get("name") or "?")[:18]
                btns.append([InlineKeyboardButton(
                    f"👤 {name}  ${b:.2f}", callback_data=f"useraction:dedbal:{u_id}", color="progress")])
            bot.send_message(uid,
                "💔 <b>កាត់ប្រាក់</b>\n━━━━━━━━━━━━━━━━━━\nជ្រើសអ្នកប្រើ:",
                parse_mode="HTML", reply_markup=InlineKeyboardMarkup(btns)); return

        if text == "👥 អ្នកប្រើប្រាស់":
            users_sorted = sorted(users_db.items(), key=lambda x: x[1].get("last",0), reverse=True)
            if not users_sorted:
                bot.send_message(uid, "❌ គ្មានអ្នកប្រើ", reply_markup=admin_kb()); return
            total = len(users_sorted)
            # Build table 20 per page to keep msgs short & avoid HTML issues
            CHUNK = 20
            chunks = [users_sorted[i:i+CHUNK] for i in range(0, total, CHUNK)]
            for page, chunk in enumerate(chunks):
                lines = []
                for i, (u_id, u_info) in enumerate(chunk, start=page*CHUNK+1):
                    b      = float(wallets.get(u_id, 0))
                    name   = (u_info.get("name") or "NoName")[:10]
                    uname  = f"@{u_info['username']}" if u_info.get("username") else "—"
                    banned = "🚫" if u_info.get("banned") else "✅"
                    lines.append(
                        f"{i:>3}. {banned} {u_id}\n"
                        f"     👤 {name}  {uname}  💳${b:.2f}"
                    )
                header = (
                    f"👥 <b>អ្នកប្រើ ({page*CHUNK+1}–{page*CHUNK+len(chunk)}/{total})</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"#    ស្ថានភាព  ID\n"
                    f"     ឈ្មោះ  Username  Balance\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                )
                # Build inline buttons for each page
                ikb_rows = []
                for u_id, _ in chunk:
                    ikb_rows.append([
                        InlineKeyboardButton(f"💸 {u_id}", callback_data=f"useraction:addbal:{u_id}", color="active"),
                        InlineKeyboardButton("💔 កាត់", callback_data=f"useraction:dedbal:{u_id}", color="progress"),
                        InlineKeyboardButton("🚫 Ban", callback_data=f"useraction:ban:{u_id}", color="inactive"),
                    ])
                ikb = InlineKeyboardMarkup(ikb_rows)
                bot.send_message(uid, header + "\n".join(lines),
                    parse_mode="HTML", reply_markup=ikb)
            bot.send_message(uid, f"✅ បង្ហាញ User ទាំង {total} នាក់រួចហើយ!", reply_markup=admin_kb())
            return

        if text == "📊 ស្ថិតិ":
            total_orders = len(smm_orders)
            total_users  = len(users_db)
            total_rev    = sum(float(o.get("price") or 0) for o in smm_orders.values())
            bot.send_message(uid,
                f"📊 <b>ស្ថិតិ</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"👥 អ្នកប្រើ: <b>{total_users}</b>\n"
                f"📊 SMM Orders: <b>{total_orders}</b>\n"
                f"💰 ចំណូលសរុប: <b>${total_rev:.2f}</b>\n"
                f"📋 Services: <b>{len(smm_services)}</b>\n"
                f"🎟️ Promos: <b>{len(promos)}</b>",
                parse_mode="HTML", reply_markup=admin_kb()); return

        if text == "📢 ផ្សព្វផ្សាយ":
            waiting[uid] = "broadcast_msg"
            bot.send_message(uid, "📢 <b>ផ្សព្វផ្សាយ</b>\nផ្ញើ Message (text/photo/video):",
                             parse_mode="HTML", reply_markup=cancel_kb()); return

        if text == "⏱ ល្បឿន Poll":
            cur = smm_poll.get("interval", 5)
            bot.send_message(uid, f"⏱ ល្បឿន Poll (បច្ចុប្បន្ន: {cur}s)",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚡ 3s",  callback_data="poll:3", color="active"),
                     InlineKeyboardButton("🟢 5s",  callback_data="poll:5", color="active"),
                     InlineKeyboardButton("🔵 10s", callback_data="poll:10", color="progress")],
                    [InlineKeyboardButton("🟡 15s", callback_data="poll:15", color="progress"),
                     InlineKeyboardButton("🔴 30s", callback_data="poll:30", color="inactive")],
                ])); return

        if text == "🖼️ Welcome Photo":
            cur = "✅ មានរូបហើយ" if welcome_cfg.get("photo_id") else "❌ មិនទាន់មានរូប"
            waiting[uid] = "set_welcome_photo"
            bot.send_message(uid,
                f"🖼️ <b>Welcome Photo</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"ស្ថានភាព: <b>{cur}</b>\n\n"
                f"📤 ផ្ញើ រូបភាព ដែលចង់ប្រើ\n"
                f"<i>(រូបនេះនឹងបង្ហាញពេល User ចុច /start)</i>",
                parse_mode="HTML", reply_markup=cancel_kb())
            return

        if step == "set_notify_channel":
            waiting.pop(uid, None)
            val = text.strip()
            if val.lower() == "off":
                notify_cfg["enabled"] = False
                _save(NOTIFY_FILE, notify_cfg)
                bot.send_message(uid, "🔕 <b>Notify Channel បានបិទ!</b>",
                    parse_mode="HTML", reply_markup=admin_kb())
            else:
                notify_cfg["channel_id"] = val
                notify_cfg["enabled"] = True
                _save(NOTIFY_FILE, notify_cfg)
                bot.send_message(uid,
                    f"✅ <b>Notify Channel បានកំណត់!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📢 Channel/Group: <code>{val}</code>\n"
                    f"ស្ថានភាព: ✅ បើក\n\n"
                    f"⚠️ <b>នៅ Render ត្រូវបន្ថែម Environment Variable:</b>\n"
                    f"<code>NOTIFY_CHANNEL_ID = {val}</code>\n\n"
                    f"<i>💡 ត្រូវប្រាកដថា Bot ជា Admin នៅ Channel/Group នោះ!</i>",
                    parse_mode="HTML", reply_markup=admin_kb())
            return

        if text == "🔔 Notify Channel":
            cid  = notify_cfg.get("channel_id", "") or "មិនទាន់កំណត់"
            ison = "✅ បើក" if notify_cfg.get("enabled") else "❌ បិទ"
            waiting[uid] = "set_notify_channel"
            bot.send_message(uid,
                f"🔔 <b>Notify Channel</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Channel/Group ID: <code>{cid}</code>\n"
                f"ស្ថានភាព: <b>{ison}</b>\n\n"
                f"📝 ផ្ញើ Channel/Group ID ថ្មី\n"
                f"<i>ឧ: <code>-1001234567890</code> ឬ <code>@mychannel</code></i>\n\n"
                f"💡 ដើម្បី <b>បិទ</b> វាយ: <code>off</code>",
                parse_mode="HTML", reply_markup=cancel_kb())
            return

        if text == "🧪 តេស្ត Notify":
            cfg = _get_notify_cfg()
            cid = cfg.get("channel_id", "")
            if not cid or not cfg.get("enabled", False):
                bot.send_message(uid, "❌ Notify Channel មិនទាន់កំណត់! ចុច 🔔 Notify Channel ដើម្បី setup ជាមុន", parse_mode="HTML", reply_markup=admin_kb())
                return
            try:
                test_msg = "🧪 តេស្ត Notify!\n━━━━━━━━━━━━━━━━━━\n✅ Bot ដំណើរការ\n📢 Channel/Group: <code>" + cid + "</code>\n━━━━━━━━━━━━━━━━━━"
                bot.send_message(cid, test_msg, parse_mode="HTML")
                bot.send_message(uid, "✅ តេស្តបានជោគជ័យ! សារបានចូល Channel/Group ✅", parse_mode="HTML", reply_markup=admin_kb())
            except Exception as e:
                bot.send_message(uid, "❌ តេស្តបរាជ័យ!\nError: <code>" + str(e) + "</code>\n\n💡 ត្រូវប្រាកដថា Bot ជា Admin នៅ Channel/Group!", parse_mode="HTML", reply_markup=admin_kb())
            return
        if text == "🔄 ធ្វើឱ្យទាន់សម័យ":
            bot.send_message(uid, "✅ បានធ្វើឱ្យទាន់សម័យ!", reply_markup=admin_kb()); return

        # ══ NEW: Settings buttons (Master Admin only) ══
        if text == "✏️ កែ Support":
            if uid != ADMIN_ID:
                bot.send_message(uid, "🚫 Master Admin only!", reply_markup=sub_admin_kb()); return
            cur_kh = support_cfg.get("kh","")
            cur_en = support_cfg.get("en","")
            kb2 = InlineKeyboardMarkup()
            kb2.add(InlineKeyboardButton("✏️ កែ (ខ្មែរ)", callback_data="set_support:kh", color="progress"))
            kb2.add(InlineKeyboardButton("✏️ Edit (English)", callback_data="set_support:en", color="progress"))
            bot.send_message(uid,
                f"💬 <b>Support Message Settings</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🇰🇭 KH:\n<code>{cur_kh or '(default)'}</code>\n\n"
                f"🇺🇸 EN:\n<code>{cur_en or '(default)'}</code>",
                parse_mode="HTML", reply_markup=kb2); return

        if text == "👥 Sub Admins":
            if uid != ADMIN_ID:
                bot.send_message(uid, "🚫 Master Admin only!", reply_markup=sub_admin_kb()); return
            kb2 = InlineKeyboardMarkup()
            kb2.add(InlineKeyboardButton("➕ បន្ថែម Sub Admin", callback_data="subadmin:add", color="active"))
            kb2.add(InlineKeyboardButton("🗑️ លុប Sub Admin", callback_data="subadmin:list_del", color="inactive"))
            lines = [f"👥 <b>Sub Admins ({len(sub_admins)})</b>\n━━━━━━━━━━━━━━━━━━"]
            if sub_admins:
                for sa in sub_admins:
                    lines.append(f"• <code>{sa}</code>")
            else:
                lines.append("(គ្មាន Sub Admin ទេ)")
            bot.send_message(uid, "\n".join(lines), parse_mode="HTML", reply_markup=kb2); return

        if text == "🔑 CamRapidPay Key":
            if uid != ADMIN_ID:
                bot.send_message(uid, "🚫 Master Admin only!", reply_markup=sub_admin_kb()); return
            cur = _effective_camrapid_key()
            masked = cur[:8] + "..." + cur[-4:] if len(cur) > 12 else cur
            kb2 = InlineKeyboardMarkup()
            kb2.add(InlineKeyboardButton("✏️ ប្តូរ Key ថ្មី", callback_data="set_camrapid:edit", color="progress"))
            kb2.add(InlineKeyboardButton("🧪 Test Key", callback_data="set_camrapid:test", color="active"))
            bot.send_message(uid,
                f"🔑 <b>CamRapidPay API Key</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Key: <code>{masked}</code>\n"
                f"Source: {'📁 runtime' if camrapid_cfg.get('key') else '⚙️ env/default'}",
                parse_mode="HTML", reply_markup=kb2); return

        if text == "📝 Welcome Msg":
            if uid != ADMIN_ID:
                bot.send_message(uid, "🚫 Master Admin only!", reply_markup=sub_admin_kb()); return
            cur = BOT_WELCOME_MSG or welcome_cfg.get("custom_msg","")
            kb2 = InlineKeyboardMarkup()
            kb2.add(InlineKeyboardButton("✏️ កែ Welcome Text", callback_data="set_welcome:text", color="progress"))
            kb2.add(InlineKeyboardButton("🗑️ Reset (default)", callback_data="set_welcome:reset", color="inactive"))
            bot.send_message(uid,
                f"📝 <b>Welcome Message</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"<code>{cur[:300] if cur else '(default)'}</code>\n\n"
                f"💡 ប្រើ <code>{{}}</code> ដើម្បីដាក់ balance",
                parse_mode="HTML", reply_markup=kb2); return

        if text == "😊 កំណត់ Emoji":
            if uid != ADMIN_ID:
                bot.send_message(uid, "🚫 Master Admin only!", reply_markup=sub_admin_kb()); return
            done_n = sum(1 for v in EMOJI_MAP.values() if v)
            bot.send_message(uid,
                f"😊 <b>Premium Emoji Settings</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"កំណត់រួច: <b>{done_n}/{len(EMOJI_MAP)}</b>\n\n"
                f"ជ្រើសសកម្មភាព:",
                parse_mode="HTML", reply_markup=emoji_menu_kb()); return

        if text.startswith("━━━"):
            bot.send_message(uid, "👇 ជ្រើស menu ខាងក្រោម:", reply_markup=admin_kb()); return

        # ── Settings waiting steps (master admin) ──
        if step == "set_support_text" or (isinstance(step, dict) and step.get("step") == "set_support_text"):
            lang_key = step["lang"] if isinstance(step, dict) else "kh"
            waiting.pop(uid, None)
            if text.strip() == "-":
                support_cfg[lang_key] = ""
                _save(SUPPORT_CFG_FILE, support_cfg)
                bot.send_message(uid, f"✅ Support Message {'(ខ្មែរ)' if lang_key=='kh' else '(English)'} reset ទៅ default!",
                                 reply_markup=admin_kb())
            else:
                support_cfg[lang_key] = text.strip()
                _save(SUPPORT_CFG_FILE, support_cfg)
                bot.send_message(uid, f"✅ Support Message {'(ខ្មែរ)' if lang_key=='kh' else '(English)'} បានរក្សា!",
                                 reply_markup=admin_kb())
            return

        if step == "subadmin_add_id":
            waiting.pop(uid, None)
            if not text.strip().lstrip("-").isdigit():
                bot.send_message(uid, "❌ ត្រូវជាលេខ Telegram ID!", reply_markup=admin_kb()); return
            new_id = int(text.strip())
            if new_id == ADMIN_ID:
                bot.send_message(uid, "⚠️ Master Admin ID មិនចាំបាច់បន្ថែម!", reply_markup=admin_kb()); return
            if new_id not in sub_admins:
                sub_admins.append(new_id)
                _save(SUB_ADMIN_FILE, sub_admins)
            bot.send_message(uid,
                f"✅ <b>Sub Admin បន្ថែម!</b>\n🆔 <code>{new_id}</code>\n"
                f"👥 ចំនួនសរុប: <b>{len(sub_admins)}</b>",
                parse_mode="HTML", reply_markup=admin_kb()); return

        if step == "set_camrapid_key":
            waiting.pop(uid, None)
            if text.strip() == "-":
                camrapid_cfg["key"] = ""
                _save(CAMRAPID_CFG_FILE, camrapid_cfg)
                bot.send_message(uid, "✅ CamRapidPay Key reset ទៅ env/default!",
                                 reply_markup=admin_kb())
            else:
                k = text.strip()
                if len(k) < 10:
                    bot.send_message(uid, "❌ Key ខ្លីពេក!", reply_markup=admin_kb()); return
                camrapid_cfg["key"] = k
                _save(CAMRAPID_CFG_FILE, camrapid_cfg)
                masked = k[:8] + "..." + k[-4:]
                bot.send_message(uid, f"✅ CamRapidPay Key ថ្មីបានរក្សា!\n🔑 <code>{masked}</code>",
                                 parse_mode="HTML", reply_markup=admin_kb())
            return

        if step == "set_welcome_msg_text":
            waiting.pop(uid, None)
            if text.strip() == "-":
                welcome_cfg.pop("custom_msg", None)
                _save(WELCOME_SETTINGS_FILE, welcome_cfg)
                bot.send_message(uid, "✅ Welcome Message reset ទៅ default!", reply_markup=admin_kb())
            else:
                welcome_cfg["custom_msg"] = text.strip()
                _save(WELCOME_SETTINGS_FILE, welcome_cfg)
                bot.send_message(uid, "✅ Welcome Message ថ្មីបានរក្សា!", reply_markup=admin_kb())
            return

        _kb_reply = admin_kb() if _is_master_admin else sub_admin_kb()
        bot.send_message(uid, "❓ ប្រើប៊ូតុង Menu ខាងក្រោម។", reply_markup=_kb_reply); return

    # ════════════════════════════════════════
    #  USER SECTION
    # ════════════════════════════════════════

    # ── Custom amount step ──
    if isinstance(step, dict) and step.get("step") == "dep_custom_amt":
        try:
            amount = float(text.replace("$","").replace(",","").strip())
            if amount <= 0: raise ValueError
        except:
            bot.send_message(uid, "❌ ចំនួនខុស! ឧ: <code>3</code> ឬ <code>7.50</code>",
                             parse_mode="HTML", reply_markup=cancel_kb()); return
        waiting.pop(uid, None)
        _process_deposit(uid, uid_str, amount, None)
        return

    # Admin confirm deposit — enter amount
    if isinstance(step, dict) and step.get("step") == "adm_confirm_dep" and uid == ADMIN_ID:
        dep_id = step.get("dep_id")
        dep    = smm_deps.get(dep_id)
        if not dep:
            bot.send_message(uid, "❌ Deposit រកមិនឃើញ", reply_markup=admin_kb())
            waiting.pop(uid, None); return
        try:
            paid = float(text.replace("$","").strip())
            if paid <= 0: raise ValueError
        except:
            bot.send_message(uid, "❌ ចំនួនខុស! ឧ: <code>5.00</code>", parse_mode="HTML"); return
        waiting.pop(uid, None)
        user_uid = int(dep["uid"])
        # Credit balance manually — recompute auto bonus against the actual paid amount
        promo_bonus = float(dep.get("promo_bonus") or 0)
        auto_bonus  = _auto_dep_bonus(paid)
        bonus = round(promo_bonus + auto_bonus, 2)
        total = round(paid + bonus, 2)
        add_bal(user_uid, total)
        smm_deps[dep_id]["status"]      = "confirmed"
        smm_deps[dep_id]["amount"]      = paid
        smm_deps[dep_id]["bonus"]       = bonus
        smm_deps[dep_id]["auto_bonus"]  = auto_bonus
        _save(SMM_DEP_FILE, smm_deps)
        new_b = bal(user_uid)
        msg = (f"✅ <b>ដាក់លុយបានជោគជ័យ!</b>\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"💰 បញ្ញើ: <b>${paid:.2f}</b>")
        if promo_bonus > 0:
            msg += f"\n🎟️ Promo Bonus: <b>+${promo_bonus:.2f}</b>"
        if auto_bonus > 0:
            msg += f"\n🎁 Auto Bonus: <b>+${auto_bonus:.2f}</b>"
        msg += f"\n💳 Balance: <b>${new_b:.2f}</b>"
        try: bot.send_message(user_uid, msg, parse_mode="HTML", reply_markup=main_kb(user_uid))
        except: pass
        bot.send_message(uid,
            f"✅ <b>Confirmed!</b>\n👤 <code>{dep['uid']}</code>\n💰 <b>${paid:.2f}</b>",
            parse_mode="HTML", reply_markup=admin_kb())
        return

    # SMM link step
    if isinstance(step, dict) and step.get("step") == "smm_link":
        slug  = step["slug"]
        qty   = step["qty"]
        price = step["price"]
        waiting.pop(uid, None)
        link  = text.strip()
        if bal(uid) < price:
            bot.send_message(uid,
                f"❌ Balance មិនគ្រប់!\n💳 ${bal(uid):.2f} | Need: ${price:.2f}",
                parse_mode="HTML", reply_markup=main_kb(uid)); return
        s = smm_services.get(slug)
        ded_bal(uid, price)
        key = smm_api.get("key",""); api_url = smm_api.get("url","")
        res = None
        if key and api_url and not s.get("manual"):
            res = _smm_api_post({"key":key,"action":"add","service":s["api_id"],"link":link,"quantity":qty})
        api_oid = str(res.get("order","")) if res else ""
        oid = _make_order_id()
        smm_orders[oid] = {
            "uid":uid_str,"slug":slug,"label":s.get("label",slug),
            "qty":qty,"price":price,"link":link,"api_order_id":api_oid,
            "status":"pending","ts":int(time.time())
        }
        _save(SMM_ORD_FILE, smm_orders)

        is_tiktok_promote = s.get("flat_price") and "tiktok" in slug.lower()
        is_manual = s.get("manual", False)

        if is_tiktok_promote:
            bot.send_message(uid,
                f"✅ <b>Order TikTok Promote បានជោគជ័យ!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <code>{oid}</code>\n"
                f"🎵 {s.get('label',slug)}\n"
                f"💰 <b>${price:.2f}</b>\n"
                f"🔗 <code>{link}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏳ <b>ចាំ Admin ដំណើរការ 5-15 នាទី</b>\n\n"
                f"📱 <b>រំឭក!</b> ចូល TikTok:\n"
                f"Inbox → System notifications\n"
                f"→ Promote Assistant → <b>Respond</b>\n"
                f"→ Authorize → <b>Confirm</b> ✅\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💳 Balance: <b>${bal(uid):.2f}</b>",
                parse_mode="HTML", reply_markup=main_kb(uid))
        else:
            bot.send_message(uid,
                f"✅ <b>បញ្ជា SMM បានជោគជ័យ!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <code>{oid}</code>\n"
                f"📊 {s.get('label',slug)}\n"
                f"🔢 ចំនួន: <b>{qty:,}</b> | 💰 <b>${price:.4f}</b>\n"
                f"🔗 <code>{link}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💳 Balance: <b>${bal(uid):.2f}</b>",
                parse_mode="HTML", reply_markup=main_kb(uid))

        # ── Notify Admin ──
        if is_tiktok_promote:
            admin_msg = (
                f"🎵 <b>TikTok Promote Order!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <code>{oid}</code>\n"
                f"👤 <code>{uid_str}</code>\n"
                f"💰 <b>${price:.2f}</b>\n"
                f"🔗 <code>{link}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 <b>Admin Steps:</b>\n"
                f"1️⃣ ចូល TikTok → video → Promote\n"
                f"2️⃣ ជ្រើស budget → ផ្ញើ invite\n"
                f"3️⃣ User នឹង Accept → ចុច ✅ Done"
            )
            kb_adm = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Done",   callback_data=f"manord:done:{oid}", color="active"),
                InlineKeyboardButton("❌ Reject", callback_data=f"manord:reject:{oid}", color="inactive"),
            ]])
            try: bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML", reply_markup=kb_adm)
            except: pass
        elif is_manual:
            admin_msg = (
                f"✍️ <b>Manual SMM Order</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <code>{oid}</code>\n"
                f"👤 <code>{uid_str}</code>\n"
                f"📊 {s.get('label',slug)}\n"
                f"🔢 {qty:,} | 💰 ${price:.4f}\n"
                f"🔗 <code>{link}</code>"
            )
            kb_adm = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Done",   callback_data=f"manord:done:{oid}", color="active"),
                InlineKeyboardButton("❌ Reject", callback_data=f"manord:reject:{oid}", color="inactive"),
            ]])
            try: bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML", reply_markup=kb_adm)
            except: pass
        else:
            try: bot.send_message(ADMIN_ID,
                f"📊 <b>SMM Order</b>\n👤 <code>{uid_str}</code> | {s.get('label',slug)} | {qty:,} | ${price:.4f}",
                parse_mode="HTML")
            except: pass
        return

    # Track order
    if step == "track_order":
        oid = text.strip().upper()
        o   = smm_orders.get(oid)
        waiting.pop(uid, None)
        if not o or o.get("uid") != uid_str:
            bot.send_message(uid, "❌ Order រកមិនឃើញ!", reply_markup=main_kb(uid)); return
        bot.send_message(uid,
            f"📊 <b>SMM Order: <code>{oid}</code></b>\n"
            f"{o.get('label','?')}\n"
            f"🔢 ចំនួន: {o.get('qty','?'):,} | 💰 ${o.get('price',0):.4f}\n"
            f"🔗 <code>{o.get('link','?')}</code>\n"
            f"📌 API: <code>{o.get('api_order_id','?')}</code>\n"
            f"✅ ស្ថានភាព: <b>{o.get('status','?')}</b>",
            parse_mode="HTML", reply_markup=main_kb(uid)); return

    # ── Main menu buttons ──
    if text in ("📊 SMM Services", "🛒 បញ្ជាទិញសេវា", "🛒 Order Service"):
        if not smm_services:
            bot.send_message(uid,
                "❌ គ្មាន SMM Service ទេ\n(Admin ចូល ⚙️ កំណត់ SMM API ដើម្បី import)",
                reply_markup=main_kb(uid)); return
        bot.send_message(uid,
            "📊 <b>SMM Services</b>\n━━━━━━━━━━━━━━━━━━\nជ្រើស Platform:",
            parse_mode="HTML", reply_markup=smm_cat_kb()); return

    if text in ("💰 ដាក់ប្រាក់", "💰 Top Up", "💸 បញ្ចូលលុយ", "💸 Top Up"):
        b = bal(uid)
        waiting.pop(uid, None)
        bonus_line = ""
        if dep_bonus_cfg.get("enabled", True) and float(dep_bonus_cfg.get("pct", 0)) > 0:
            min_amt = float(dep_bonus_cfg.get("min_amount", 1.0))
            pct     = float(dep_bonus_cfg.get("pct", 5.0))
            bonus_line = (
                f"\n🎁 <i>ដាក់ចាប់ពី ${min_amt:.2f} ឡើងទៅ ទទួល Bonus {pct:.0f}% ភ្លាមៗ!</i>\n"
                if lang == "kh" else
                f"\n🎁 <i>Deposit ${min_amt:.2f}+ and get {pct:.0f}% bonus instantly!</i>\n"
            )
        bot.send_message(uid,
            f"💸 <b>{'ដាក់លុយ' if lang=='kh' else 'Top Up'}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💳 Balance: <b>${b:.2f}</b>\n"
            f"━━━━━━━━━━━━━━━━━━{bonus_line}\n"
            f"{'ជ្រើស ចំនួន:' if lang=='kh' else 'Choose Amount:'}",
            parse_mode="HTML", reply_markup=deposit_amt_kb(uid)); return

    if text in ("📦 ការបញ្ជា", "📦 Orders", "📋 ប្រវត្តិការបញ្ជាទិញ", "📋 Order History"):
        my_orders = {oid: o for oid, o in smm_orders.items() if o.get("uid") == uid_str}
        if not my_orders:
            bot.send_message(uid,
                "📦 <b>ការបញ្ជា</b>\n\n❌ គ្មាន Order ទេ!",
                parse_mode="HTML", reply_markup=main_kb(uid)); return
        lines = ["📦 <b>ការបញ្ជា SMM</b>\n━━━━━━━━━━━━━━━━━━"]
        for oid, o in sorted(my_orders.items(), key=lambda x: x[1].get("ts",0), reverse=True)[:10]:
            lines.append(f"📊 <code>{oid}</code> — {o.get('label','?')} x{o.get('qty','?')} | ${o.get('price',0):.4f} | {o.get('status','?')}")
        bot.send_message(uid, "\n".join(lines), parse_mode="HTML", reply_markup=main_kb(uid)); return

    if text in ("📋 ប្រវត្តិ", "📋 History"):
        my_orders = {oid: o for oid, o in smm_orders.items() if o.get("uid") == uid_str}
        if not my_orders:
            bot.send_message(uid,
                "📋 <b>ប្រវត្តិ</b>\n\n❌ គ្មាន Order ទេ!",
                parse_mode="HTML", reply_markup=main_kb(uid)); return
        lines = ["📋 <b>ប្រវត្តិ</b>\n━━━━━━━━━━━━━━━━━━"]
        for oid, o in sorted(my_orders.items(), key=lambda x: x[1].get("ts",0), reverse=True)[:15]:
            dt = datetime.datetime.fromtimestamp(o.get("ts",0)).strftime("%d/%m %H:%M")
            lines.append(f"📊 <code>{oid}</code> | {o.get('label','?')} x{o.get('qty','?')} | ${o.get('price',0):.4f} | {o.get('status','?')} | {dt}")
        bot.send_message(uid, "\n".join(lines)[:4000], parse_mode="HTML", reply_markup=main_kb(uid)); return

    if text in ("👜 កាបូបលុយ", "👜 Wallet", "👤 តំណាំការគណនី", "👤 គណនី", "👤 My Account"):
        waiting.pop(uid, None)
        b = bal(uid)
        my_deps = [(k, v) for k, v in smm_deps.items() if v.get("uid") == uid_str]
        confirmed = sum(float(v.get("amount") or 0) for _, v in my_deps if v.get("status") == "confirmed")
        pending   = sum(float(v.get("amount") or 0) for _, v in my_deps if v.get("status") == "pending")
        total_orders = sum(1 for o in smm_orders.values() if o.get("uid") == uid_str)
        u = users_db.get(uid_str, {})
        name = u.get("name", "") or ""
        uname = f"@{u['username']}" if u.get("username") else ""
        if lang == "kh":
            msg = (
                f"👤 <b>គណនីរបស់ខ្ញុំ</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🙍 ឈ្មោះ: <b>{name}</b>  {uname}\n"
                f"🆔 ID: <code>{uid_str}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💳 Balance: <b>${b:.2f}</b>\n"
                f"✅ សរុបដាក់: <b>${confirmed:.2f}</b>\n"
                f"⏳ រង់ចាំ: <b>${pending:.2f}</b>\n"
                f"📦 Orders: <b>{total_orders}</b>"
            )
        else:
            msg = (
                f"👤 <b>My Account</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🙍 Name: <b>{name}</b>  {uname}\n"
                f"🆔 ID: <code>{uid_str}</code>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💳 Balance: <b>${b:.2f}</b>\n"
                f"✅ Total deposited: <b>${confirmed:.2f}</b>\n"
                f"⏳ Pending: <b>${pending:.2f}</b>\n"
                f"📦 Orders: <b>{total_orders}</b>"
            )
        bot.send_message(uid, msg, parse_mode="HTML", reply_markup=main_kb(uid)); return

    if text in ("Track 🔍", "🔍 Track Order", "🔍 តាមដានការបញ្ជាទិញ"):
        bot.send_message(uid,
            "🔍 <b>តាមដាន Order</b>\nផ្ញើ Order ID (ឧ: KZ12345):",
            parse_mode="HTML", reply_markup=cancel_kb())
        waiting[uid] = "track_order"; return

    if text in ("💬 Support", "💬 ជំនួយ"):
        lang = get_lang(uid)
        custom = support_cfg.get(lang) or support_cfg.get("kh") or ""
        msg = custom if custom else t(uid, "support_msg")
        bot.send_message(uid, msg, parse_mode="HTML", reply_markup=main_kb(uid)); return

    if text in ("💡 របៀបប្រើប្រាស់", "💡 How to Use"):
        bot.send_message(uid, t(uid, "how_to_use"), parse_mode="HTML", reply_markup=main_kb(uid)); return

    bot.send_message(uid, t(uid, "fallback"), reply_markup=main_kb(uid))

# ═══════════════════════════════════════════════════════════
#  FLASK CONTROL SERVER
# ═══════════════════════════════════════════════════════════
flask_app = Flask(__name__)

def _check_key():
    key = flask_request.args.get("key") or (flask_request.get_json(silent=True) or {}).get("key")
    return key == CONTROL_KEY

@flask_app.route("/health")
def health():
    return jsonify({"status": "running", "bot": "Kaijaklike"})

@flask_app.route("/status")
def status():
    if not _check_key():
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({
        "status": "running",
        "users": len(users_db),
        "smm_orders": len(smm_orders),
        "smm_services": len(smm_services),
        "wallets": len(wallets),
    })

@flask_app.route("/shutdown", methods=["GET", "POST"])
def shutdown():
    if not _check_key():
        return jsonify({"error": "Unauthorized"}), 403
    logger.warning("🛑 Shutdown requested!")
    try:
        bot.send_message(ADMIN_ID, "🛑 <b>Bot កំពុងបិទ...</b>", parse_mode="HTML")
        time.sleep(1)
    except: pass
    def _stop():
        time.sleep(0.5)
        bot.stop_polling()
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=_stop, daemon=True).start()
    return jsonify({"status": "shutting_down"})

@flask_app.route("/restart", methods=["GET", "POST"])
def restart():
    if not _check_key():
        return jsonify({"error": "Unauthorized"}), 403
    logger.warning("🔄 Restart requested!")
    try:
        bot.send_message(ADMIN_ID, "🔄 <b>Bot កំពុង Restart...</b>", parse_mode="HTML")
        time.sleep(1)
    except: pass
    def _restart():
        time.sleep(0.5)
        bot.stop_polling()
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    threading.Thread(target=_restart, daemon=True).start()
    return jsonify({"status": "restarting"})

@flask_app.route("/broadcast_web", methods=["POST"])
def broadcast_web():
    if not _check_key():
        return jsonify({"error": "Unauthorized"}), 403
    data = flask_request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    sent = failed = 0
    for u_id in list(users_db.keys()):
        try:
            bot.send_message(int(u_id), text, parse_mode="HTML")
            sent += 1
        except: failed += 1
        time.sleep(0.05)
    return jsonify({"sent": sent, "failed": failed})

def run_flask():
    logger.info(f"🌐 Control Server running on port {CONTROL_PORT}")
    flask_app.run(host="0.0.0.0", port=CONTROL_PORT, debug=False, use_reloader=False)

def _self_ping():
    """Ping self every 5 min to prevent Render free tier spin down"""
    import urllib.request
    while True:
        try:
            time.sleep(300)  # 5 minutes
            render_url = os.getenv("RENDER_EXTERNAL_URL", "")
            if render_url:
                urllib.request.urlopen(f"{render_url}/health", timeout=10)
                logger.info("✅ Self-ping OK")
        except Exception as e:
            logger.warning(f"⚠️ Self-ping failed: {e}")

def _bot_polling_with_retry():
    """Polling with auto-reconnect on network error"""
    while True:
        try:
            logger.info("🤖 Bot polling ចាប់ផ្ដើម...")
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            logger.warning(f"⚠️ Polling error: {e} — Retry in 10s...")
            time.sleep(10)

# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info(f"🚀 Kaijaklike Bot [{INSTANCE_NAME or 'MASTER'}] កំពុងចាប់ផ្ដើម...")
    logger.info(f"🔑 Control Key: {CONTROL_KEY}  ← ដូរនៅ CONTROL_KEY!")
    logger.info(f"📊 Services loaded: {len(smm_services)}")
    _warm_stripped_text_map()
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=_self_ping, daemon=True).start()
    if IS_MASTER:
        for _cln_name, _cln_cfg in clone_registry.items():
            try:
                _spawn_clone(_cln_name, _cln_cfg)
                logger.info(f"🤖 Autostart clone '{_cln_name}' on port {_cln_cfg['port']}")
            except Exception as _e:
                logger.error(f"Autostart clone '{_cln_name}' failed: {_e}")
        threading.Thread(target=_clone_watchdog, daemon=True).start()
    _bot_polling_with_retry()
