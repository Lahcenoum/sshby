import sqlite3
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes

# استيراد من ملف الإعدادات
from bot_config import DB_FILE, TEXTS, ADMIN_CONTACT_INFO

def get_text(key: str, lang_code: str = 'ar') -> str:
    """
    يجلب النص من قاموس النصوص بناءً على لغة المستخدم.
    """
    if lang_code not in TEXTS:
        lang_code = 'ar' # اللغة الافتراضية
    return TEXTS[lang_code].get(key, f"_{key}_")

def get_user_lang(user_id: int) -> str:
    """
    يحصل على كود اللغة للمستخدم من قاعدة البيانات.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            res = conn.execute("SELECT language_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
            return res[0] if res else 'ar'
    except Exception:
        return 'ar'

def set_user_lang(user_id: int, lang_code: str):
    """
    يحدّث لغة المستخدم في قاعدة البيانات.
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE users SET language_code = ? WHERE telegram_user_id = ?", (lang_code, user_id))
        conn.commit()

def get_connection_setting(key: str) -> str:
    """
    يحصل على إعدادات الاتصال (مثل الهوست والبورت) من قاعدة البيانات.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            result = conn.execute("SELECT value FROM connection_settings WHERE key = ?", (key,)).fetchone()
            return result[0] if result else ""
    except Exception:
        return ""

def set_connection_setting(key: str, value: str):
    """
    يحفظ إعدادات الاتصال في قاعدة البيانات.
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def log_activity(func):
    """
    Decorator لتسجيل آخر نشاط للمستخدم.
    """
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user:
            user_id = update.effective_user.id
            today = date.today().isoformat()
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT OR REPLACE INTO daily_activity (user_id, last_seen_date) VALUES (?, ?)", (user_id, today))
                conn.commit()
        return await func(update, context, *args, **kwargs)
    return wrapper

def init_db():
    """
    يقوم بإنشاء جميع الجداول اللازمة في قاعدة البيانات عند بدء تشغيل البوت.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # إنشاء الجداول
        cursor.execute('CREATE TABLE IF NOT EXISTS users (telegram_user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, last_daily_claim DATE, join_bonus_claimed INTEGER DEFAULT 0, language_code TEXT DEFAULT "ar", created_date DATE, referrer_id INTEGER)')
        cursor.execute('CREATE TABLE IF NOT EXISTS ssh_accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_user_id INTEGER NOT NULL, ssh_username TEXT NOT NULL UNIQUE, ssh_password TEXT NOT NULL, created_at TIMESTAMP NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS reward_channels (channel_id INTEGER PRIMARY KEY, channel_link TEXT NOT NULL, reward_points INTEGER NOT NULL, channel_name TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS user_channel_rewards (telegram_user_id INTEGER, channel_id INTEGER, PRIMARY KEY (telegram_user_id, channel_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS redeem_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
        cursor.execute('CREATE TABLE IF NOT EXISTS redeemed_users (code TEXT, telegram_user_id INTEGER, PRIMARY KEY (code, telegram_user_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS daily_activity (user_id INTEGER PRIMARY KEY, last_seen_date DATE NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS connection_settings (key TEXT PRIMARY KEY, value TEXT)')
        
        # إضافة الإعدادات الافتراضية إذا لم تكن موجودة
        default_settings = {
            "hostname": "your.hostname.com",
            "ws_ports": "80, 8880, 2053",
            "ssl_port": "443",
            "udpcustom_port": "7300",
            "admin_contact": ADMIN_CONTACT_INFO,
            "payload": "your.default.payload"
        }
        for key, value in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        print("Database initialized successfully.")

