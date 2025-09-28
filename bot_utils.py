import sqlite3
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes

# --- استيراد الإعدادات الضرورية ---
from bot_config import DB_FILE, TEXTS

# =================================================================================
#  دوال النصوص واللغات
# =================================================================================
def get_text(key, lang_code='ar'):
    """
    تجلب نصًا معينًا من قاموس النصوص بناءً على لغة المستخدم.
    """
    if lang_code not in TEXTS:
        lang_code = 'ar'
    # Fallback to Arabic if the key doesn't exist in the selected language
    return TEXTS[lang_code].get(key, TEXTS['ar'].get(key, key))

# =================================================================================
#  دوال التعامل مع قاعدة البيانات
# =================================================================================
def get_user_lang(user_id):
    """
    تجلب كود اللغة الخاص بالمستخدم من قاعدة البيانات.
    """
    with sqlite3.connect(DB_FILE) as conn:
        res = conn.execute("SELECT language_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
        return res[0] if res else 'ar'

def set_user_lang(user_id, lang_code):
    """
    تُحدّث لغة المستخدم في قاعدة البيانات.
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE users SET language_code = ? WHERE telegram_user_id = ?", (lang_code, user_id))
        conn.commit()

def get_connection_setting(key):
    """
    تجلب إعدادات الاتصال (مثل الهوست والبورتات) من قاعدة البيانات.
    """
    with sqlite3.connect(DB_FILE) as conn:
        result = conn.execute("SELECT value FROM connection_settings WHERE key = ?", (key,)).fetchone()
        return result[0] if result else ""

def set_connection_setting(key, value):
    """
    تحفظ أو تُحدّث إعدادات الاتصال في قاعدة البيانات.
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

# =================================================================================
#  دوال مساعدة عامة (Helpers)
# =================================================================================
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
