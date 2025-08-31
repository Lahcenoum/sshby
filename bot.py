import sys
import subprocess
import random
import string
import sqlite3
import re
import traceback
import html
import json
import uuid
from datetime import datetime, date, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LabeledPrice
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler, PreCheckoutQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_USER_ID = 5344028088
ADMIN_CONTACT_INFO = "@YourAdminUsername"
DB_FILE = 'ssh_bot_users.db'

# --- إعدادات الدفع (Payment Settings) ---
# احصل على هذا الرمز من @BotFather بعد توصيل بوابة الدفع
PAYPAL_PROVIDER_TOKEN = "5775769170:LIVE:TG_CYP78fu5BaV6RXYeJ2NO3RgA"
PAYMENT_CURRENCY = "USD"
# السعر بالوحدة الأصغر (سنت)، لذا 250 تعادل $2.50
PAYPAL_PAYMENT_OPTIONS = [LabeledPrice(label="سيرفر مدفوع (30 يوم)", amount=250)]
# السعر بالنجوم يعادل تقريباً 2.5 دولار أمريكي (قد يختلف السعر قليلاً حسب تليجرام)
STARS_PAYMENT_OPTIONS = [LabeledPrice(label="سيرفر مدفوع (30 يوم)", amount=1050)]


# --- إعدادات SSH ---
SSH_SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
SSH_ACCOUNT_EXPIRY_DAYS = 2 # للحسابات المجانية
PAID_SSH_ACCOUNT_EXPIRY_DAYS = 30 # للحسابات المدفوعة

# --- قيم نظام النقاط ---
COST_PER_ACCOUNT = 2
DAILY_LOGIN_BONUS = 1
INITIAL_POINTS = 2
JOIN_BONUS = 0
REFERRAL_BONUS = 2

# --- إعدادات القنوات ---
REQUIRED_CHANNEL_ID = -1001932589296
REQUIRED_GROUP_ID = -1002218671728
CHANNEL_LINK = "https://t.me/CLOUDVIP"
GROUP_LINK = "https://t.me/dgtliA"

# Conversation handler states
(ADD_CHANNEL_NAME, ADD_CHANNEL_LINK, ADD_CHANNEL_ID, ADD_CHANNEL_POINTS) = range(4)
(CREATE_CODE_NAME, CREATE_CODE_POINTS, CREATE_CODE_USES) = range(4, 7)
(REDEEM_CODE_INPUT,) = range(7, 8)
(EDIT_HOSTNAME, EDIT_WS_PORTS, EDIT_SSL_PORT, EDIT_UDPCUSTOM, EDIT_ADMIN_CONTACT, EDIT_PAYLOAD) = range(8, 14)

# =================================================================================
# 2. دعم اللغات (Localization)
# =================================================================================
TEXTS = {
    'ar': {
        "welcome": "أهلاً بك في بوت الخدمات!\n\nاستخدم الأزرار أدناه لطلب حساب SSH.",
        "get_account_button": "🎁 حساب مجاني (نقاط)",
        "my_account_button": "👤 حساباتي",
        "balance_button": "💰 رصيدي",
        "earn_points_button": "🎁 كسب النقاط",
        "redeem_code_button": "🎁 استرداد كود",
        "daily_button": "☀️ مكافأة يومية",
        "referral_button": "👥 دعوة صديق",
        "contact_admin_button": "👨‍💻 تواصل مع الأدمن",
        "choose_account_type": "اختر نوع الحساب الذي تريده:",
        "ssh_account_button": "🌐 حساب SSH",
        "v2ray_account_button": "🚀 حساب V2Ray (قيد التطوير)",
        "udpcustom_account_button": "⚡️ حساب UDP Custom (قيد التطوير)",
        "under_development": "🚧 هذه الميزة قيد التطوير حاليًا.",
        "contact_admin_info": "للتواصل مع الأدمن، يرجى مراسلة: {contact_info}",
        "not_enough_points": "⚠️ ليس لديك نقاط كافية. التكلفة هي <b>{cost}</b> نقطة.",
        "creation_error": "❌ حدث خطأ أثناء إنشاء الحساب. قد يكون لديك حساب بالفعل أو خطأ آخر.",
        "force_join_prompt": "❗️لاستخدام البوت، يجب عليك الانضمام إلى قناتنا ومجموعتنا أولاً.\n\nبعد الانضمام، اضغط على زر '✅ تحققت'.",
        "force_join_channel_button": "📢 انضم للقناة",
        "force_join_group_button": "👥 انضم للمجموعة",
        "force_join_verify_button": "✅ تحققت",
        "force_join_success": "✅ شكرًا لانضمامك! يمكنك الآن استخدام البوت.",
        "force_join_fail": "❌ لم يتم التحقق من انضمامك. يرجى التأكد من انضمامك لكليهما والمحاولة مرة أخرى.",
        "join_bonus_awarded": "🎉 مكافأة الانضمام! لقد حصلت على {bonus} نقطة.",
        "balance_info": "💰 رصيدك الحالي هو: <b>{points}</b> نقطة.",
        "daily_bonus_claimed": "🎉 لقد حصلت على مكافأتك اليومية: <b>{bonus}</b> نقطة! رصيدك الآن هو <b>{new_balance}</b>.",
        "daily_bonus_already_claimed": "ℹ️ لقد حصلت بالفعل على مكافأتك اليومية. تعال غدًا!",
        "no_accounts_found": "ℹ️ لم يتم العثور على أي حسابات نشطة مرتبطة بك.",
        "your_accounts": "<b>👤 حسابات SSH الخاصة بك:</b>",
        "account_details_full": "🏷️ <b>اسم المستخدم:</b> <code>{username}</code>\n🔑 <b>كلمة المرور:</b> <code>{password}</code>\n🗓️ <b>تاريخ انتهاء الصلاحية:</b> <code>{expiry}</code>\n\n<b>Hostname:</b> <code>{hostname}</code>\n<b>Websocket Ports:</b> <code>{ws_ports}</code>\n<b>SSL Port:</b> <code>{ssl_port}</code>\n<b>UDPCUSTOM Port:</b> <code>{udpcustom_port}</code>\n\n<b>Payload:</b>\n<pre><code>{payload}</code></pre>",
        "rewards_header": "اختر طريقة لكسب النقاط:",
        "verify_join_button": "✅ تحقق من الانضمام",
        "reward_success": "🎉 رائع! لقد حصلت على {points} نقطة.",
        "reward_fail": "❌ لم تنضم بعد. حاول مرة أخرى بعد الانضمام.",
        "no_channels_available": "ℹ️ لا توجد قنوات متاحة للمكافآت حاليًا.",
        "redeem_prompt": "يرجى إرسال الكود الذي تريد استرداده.",
        "redeem_success": "🎉 تهانينا! لقد حصلت على <b>{points}</b> نقطة. رصيدك الآن هو <b>{new_balance}</b>.",
        "redeem_invalid_code": "❌ هذا الكود غير صالح أو غير موجود.",
        "redeem_limit_reached": "❌ لقد وصل هذا الكود إلى الحد الأقصى من الاستخدام.",
        "redeem_already_used": "❌ لقد قمت بالفعل باستخدام هذا الكود.",
        "referral_info": "👥 <b>نظام الإحالة</b>\n\nادعُ أصدقاءك للانضمام إلى البوت باستخدام رابط الإحالة الخاص بك، واحصل على <b>{bonus}</b> نقطة عن كل صديق ينضم!\n\n🔗 <b>رابطك الخاص:</b>\n<code>{link}</code>",
        "referral_bonus_notification": "🎉 لقد حصلت على <b>{bonus}</b> نقطة من دعوة صديق جديد!",
        "admin_panel_header": "⚙️ لوحة تحكم الأدمن",
        "admin_return_button": "⬅️ عودة",
        "admin_manage_rewards_button": "📢 إدارة قنوات الربح",
        "admin_manage_codes_button": "🎁 إدارة أكواد الهدايا",
        "admin_user_stats_button": "📊 إحصائيات المستخدمين",
        "admin_edit_connection_info_button": "⚙️ تعديل معلومات الاتصال",
        "admin_add_channel_button": "➕ إضافة قناة/مجموعة",
        "admin_remove_channel_button": "➖ إزالة قناة/مجموعة",
        "admin_add_channel_name_prompt": "أرسل اسم القناة:",
        "admin_add_channel_link_prompt": "الآن أرسل رابط القناة الكامل:",
        "admin_add_channel_id_prompt": "أرسل معرف القناة الرقمي (يبدأ بـ -100):",
        "admin_add_channel_points_prompt": "أخيراً، أرسل عدد نقاط المكافأة:",
        "admin_channel_added_success": "✅ تم إضافة القناة بنجاح.",
        "admin_remove_channel_prompt": "اختر القناة التي تريد إزالتها:",
        "admin_channel_removed_success": "🗑️ تم إزالة القناة بنجاح.",
        "admin_create_code_button": "➕ إنشاء كود جديد",
        "admin_create_code_prompt_name": "أرسل اسم الكود الجديد (مثال: WELCOME2025):",
        "admin_create_code_prompt_points": "الآن أرسل عدد النقاط التي يمنحها هذا الكود:",
        "admin_create_code_prompt_uses": "أخيراً، أرسل عدد المستخدمين الذين يمكنهم استخدام هذا الكود:",
        "admin_code_created": "✅ تم إنشاء الكود <code>{code}</code> بنجاح. يمنح <b>{points}</b> نقطة ومتاح لـ <b>{uses}</b> مستخدمين.",
        "admin_edit_hostname_prompt": "أرسل الـ Hostname الجديد:",
        "admin_edit_ws_ports_prompt": "أرسل بورتات Websocket الجديدة (مثال: 80, 8880):",
        "admin_edit_ssl_port_prompt": "أرسل بورت SSL الجديد:",
        "admin_edit_udpcustom_prompt": "أرسل بورت UDPCUSTOM الجديد:",
        "admin_edit_contact_prompt": "أرسل معلومات التواصل الجديدة (مثال: @username):",
        "admin_edit_payload_prompt": "أخيراً، أرسل الـ Payload الجديد:",
        "admin_info_updated_success": "✅ تم تحديث معلومات الاتصال بنجاح.",
        "user_stats_info": "<b>📊 إحصائيات المستخدمين:</b>\n\n- <b>إجمالي المستخدمين:</b> {total_users}\n- <b>النشطون اليوم:</b> {active_today}\n- <b>النشطون أمس:</b> {active_yesterday}\n- <b>المستخدمون الجدد اليوم:</b> {new_today}",
        "choose_language": "اختر لغتك المفضلة:",
        "language_set": "✅ تم تعيين اللغة إلى: {lang_name}",
        "invalid_input": "❌ إدخال غير صالح، يرجى المحاولة مرة أخرى.",
        "operation_cancelled": "✅ تم إلغاء العملية.",
        "creating_account": "جاري إنشاء الحساب...",
        "points": "نقاط",
        "paid_servers_button": "💳 سيرفرات مدفوعة",
        "choose_payment_method": "اختر طريقة الدفع للحصول على سيرفر مدفوع (30 يومًا):",
        "paypal_button": "💳 PayPal - $2.5",
        "telegram_stars_button": "⭐ نجوم تليجرام - 1050 نجمة",
        "moroccan_bank_button": "🏦 تحويل بنكي مغربي",
        "bank_transfer_details": """
<b>للدفع عبر تحويل بنكي مغربي:</b>

المرجو تحويل مبلغ <b>25 درهم مغربي</b> إلى أحد الحسابات التالية:

<b>CIH Bank:</b>
- <b>صاحب الحساب:</b> [هنا تضع اسم صاحب الحساب]
- <b>رقم الحساب (RIB):</b> <code>[هنا تضع رقم الحساب الكامل]</code>

<b>BMCE Bank (Bank of Africa):</b>
- <b>صاحب الحساب:</b> [هنا تضع اسم صاحب الحساب]
- <b>رقم الحساب (RIB):</b> <code>[هنا تضع رقم الحساب الكامل]</code>

بعد إتمام الدفع، يرجى إرسال لقطة شاشة للإيصال مع رقم الحساب الذي استخدمته في التحويل إلى رقم الواتساب التالي للتحقق وتفعيل حسابك:
📱 <b>WhatsApp:</b> <code>[هنا تضع رقم الواتساب]</code>
""",
        "payment_invoice_title": "سيرفر SSH مدفوع",
        "payment_invoice_description": "اشتراك لمدة 30 يومًا في سيرفر SSH عالي السرعة.",
        "payment_not_configured": "عذراً، طريقة الدفع هذه غير مهيأة بعد. يرجى التواصل مع الأدمن.",
        "payment_successful_creation": "✅ تم الدفع بنجاح! تفاصيل حسابك:",
    },
    'en': {
        "welcome": "Welcome to the Services Bot!\n\nUse the buttons below to request an SSH account.",
        "get_account_button": "🎁 Free Account (Points)",
        "my_account_button": "👤 My Accounts",
        "balance_button": "💰 My Balance",
        "earn_points_button": "🎁 Earn Points",
        "redeem_code_button": "🎁 Redeem Code",
        "daily_button": "☀️ Daily Bonus",
        "referral_button": "👥 Refer a Friend",
        "contact_admin_button": "👨‍💻 Contact Admin",
        "choose_account_type": "Choose the type of account you want:",
        "ssh_account_button": "🌐 SSH Account",
        "v2ray_account_button": "🚀 V2Ray Account (Under Development)",
        "udpcustom_account_button": "⚡️ UDP Custom Account (Under Development)",
        "under_development": "🚧 This feature is currently under development.",
        "contact_admin_info": "To contact the admin, please message: {contact_info}",
        "not_enough_points": "⚠️ You don't have enough points. The cost is <b>{cost}</b> points.",
        "creation_error": "❌ An error occurred while creating the account. You might already have an account or another error occurred.",
        "force_join_prompt": "❗️To use the bot, you must first join our channel and group.\n\nAfter joining, press the '✅ I have joined' button.",
        "force_join_channel_button": "📢 Join Channel",
        "force_join_group_button": "👥 Join Group",
        "force_join_verify_button": "✅ I have joined",
        "force_join_success": "✅ Thank you for joining! You can now use the bot.",
        "force_join_fail": "❌ Your membership could not be verified. Please make sure you have joined both and try again.",
        "join_bonus_awarded": "🎉 Join bonus! You have received {bonus} points.",
        "balance_info": "💰 Your current balance is: <b>{points}</b> points.",
        "daily_bonus_claimed": "🎉 You have claimed your daily bonus: <b>{bonus}</b> points! Your new balance is <b>{new_balance}</b>.",
        "daily_bonus_already_claimed": "ℹ️ You have already claimed your daily bonus. Come back tomorrow!",
        "no_accounts_found": "ℹ️ No active accounts found for you.",
        "your_accounts": "<b>👤 Your SSH Accounts:</b>",
        "account_details_full": "🏷️ <b>Username:</b> <code>{username}</code>\n🔑 <b>Password:</b> <code>{password}</code>\n🗓️ <b>Expiry Date:</b> <code>{expiry}</code>\n\n<b>Hostname:</b> <code>{hostname}</code>\n<b>Websocket Ports:</b> <code>{ws_ports}</code>\n<b>SSL Port:</b> <code>{ssl_port}</code>\n<b>UDPCUSTOM Port:</b> <code>{udpcustom_port}</code>\n\n<b>Payload:</b>\n<pre><code>{payload}</code></pre>",
        "rewards_header": "Choose a way to earn points:",
        "verify_join_button": "✅ Verify Join",
        "reward_success": "🎉 Great! You have earned {points} points.",
        "reward_fail": "❌ You haven't joined yet. Try again after joining.",
        "no_channels_available": "ℹ️ No reward channels are available at the moment.",
        "redeem_prompt": "Please send the code you want to redeem.",
        "redeem_success": "🎉 Congratulations! You have received <b>{points}</b> points. Your new balance is <b>{new_balance}</b>.",
        "redeem_invalid_code": "❌ This code is invalid or does not exist.",
        "redeem_limit_reached": "❌ This code has reached its maximum usage limit.",
        "redeem_already_used": "❌ You have already used this code.",
        "referral_info": "👥 <b>Referral System</b>\n\nInvite your friends to join the bot using your referral link and get <b>{bonus}</b> points for each friend who joins!\n\n🔗 <b>Your Link:</b>\n<code>{link}</code>",
        "referral_bonus_notification": "🎉 You have received <b>{bonus}</b> points from a new referral!",
        "admin_panel_header": "⚙️ Admin Panel",
        "admin_return_button": "⬅️ Back",
        "admin_manage_rewards_button": "📢 Manage Reward Channels",
        "admin_manage_codes_button": "🎁 Manage Gift Codes",
        "admin_user_stats_button": "📊 User Statistics",
        "admin_edit_connection_info_button": "⚙️ Edit Connection Info",
        "admin_add_channel_button": "➕ Add Channel/Group",
        "admin_remove_channel_button": "➖ Remove Channel/Group",
        "admin_add_channel_name_prompt": "Send the channel name:",
        "admin_add_channel_link_prompt": "Now send the full channel link:",
        "admin_add_channel_id_prompt": "Send the numeric channel ID (starts with -100):",
        "admin_add_channel_points_prompt": "Finally, send the number of reward points:",
        "admin_channel_added_success": "✅ Channel added successfully.",
        "admin_remove_channel_prompt": "Choose the channel you want to remove:",
        "admin_channel_removed_success": "🗑️ Channel removed successfully.",
        "admin_create_code_button": "➕ Create New Code",
        "admin_create_code_prompt_name": "Send the new code name (e.g., WELCOME2025):",
        "admin_create_code_prompt_points": "Now send the number of points this code grants:",
        "admin_create_code_prompt_uses": "Finally, send the number of users who can use this code:",
        "admin_code_created": "✅ Code <code>{code}</code> created successfully. It grants <b>{points}</b> points and is available for <b>{uses}</b> users.",
        "admin_edit_hostname_prompt": "Send the new Hostname:",
        "admin_edit_ws_ports_prompt": "Send the new Websocket ports (e.g., 80, 8880):",
        "admin_edit_ssl_port_prompt": "Send the new SSL port:",
        "admin_edit_udpcustom_prompt": "Send the new UDPCUSTOM port:",
        "admin_edit_contact_prompt": "Send the new contact info (e.g., @username):",
        "admin_edit_payload_prompt": "Finally, send the new Payload:",
        "admin_info_updated_success": "✅ Connection info updated successfully.",
        "user_stats_info": "<b>📊 User Statistics:</b>\n\n- <b>Total Users:</b> {total_users}\n- <b>Active Today:</b> {active_today}\n- <b>Active Yesterday:</b> {active_yesterday}\n- <b>New Users Today:</b> {new_today}",
        "choose_language": "Choose your preferred language:",
        "language_set": "✅ Language set to: {lang_name}",
        "invalid_input": "❌ Invalid input, please try again.",
        "operation_cancelled": "✅ Operation cancelled.",
        "creating_account": "Creating account...",
        "points": "Points",
        "paid_servers_button": "💳 Paid Servers",
        "choose_payment_method": "Choose a payment method for a paid server (30 days):",
        "paypal_button": "💳 PayPal - $2.50",
        "telegram_stars_button": "⭐ Telegram Stars - 1050 Stars",
        "moroccan_bank_button": "🏦 Moroccan Bank Transfer",
        "bank_transfer_details": """
<b>To pay via Moroccan bank transfer:</b>

Please transfer <b>25 MAD</b> to one of the following accounts:

<b>CIH Bank:</b>
- <b>Account Holder:</b> [Account Holder Name]
- <b>Account Number (RIB):</b> <code>123456789012345678901234</code>

<b>BMCE Bank (Bank of Africa):</b>
- <b>Account Holder:</b> [Account Holder Name]
- <b>Account Number (RIB):</b> <code>987654321098765432109876</code>

After completing the payment, please send a screenshot of the receipt along with the account number you used for the transfer to the following WhatsApp number for verification and activation:
📱 <b>WhatsApp:</b> <code>+212600000000</code>
""",
        "payment_invoice_title": "Paid SSH Server",
        "payment_invoice_description": "30-day subscription for a high-speed SSH server.",
        "payment_not_configured": "Sorry, this payment method is not configured yet. Please contact the admin.",
        "payment_successful_creation": "✅ Payment successful! Your account details:",
    }
}

def get_text(key, lang_code='ar'):
    # Default to 'ar' if the language code is not supported
    if lang_code not in TEXTS:
        lang_code = 'ar'
    # Try to get the text in the specified language, fallback to Arabic if the key is missing
    return TEXTS[lang_code].get(key, TEXTS['ar'].get(key, key))

# =================================================================================
# 3. إدارة قاعدة البيانات (Database Management)
# =================================================================================
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (telegram_user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, last_daily_claim DATE, join_bonus_claimed INTEGER DEFAULT 0, language_code TEXT DEFAULT "ar", created_date DATE, referrer_id INTEGER)')
        cursor.execute('CREATE TABLE IF NOT EXISTS ssh_accounts (id INTEGER PRIMARY KEY, telegram_user_id INTEGER NOT NULL, ssh_username TEXT NOT NULL, ssh_password TEXT NOT NULL, created_at TIMESTAMP NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS reward_channels (channel_id INTEGER PRIMARY KEY, channel_link TEXT NOT NULL, reward_points INTEGER NOT NULL, channel_name TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS user_channel_rewards (telegram_user_id INTEGER, channel_id INTEGER, PRIMARY KEY (telegram_user_id, channel_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS redeem_codes (code TEXT PRIMARY KEY, points INTEGER, max_uses INTEGER, current_uses INTEGER DEFAULT 0)')
        cursor.execute('CREATE TABLE IF NOT EXISTS redeemed_users (code TEXT, telegram_user_id INTEGER, PRIMARY KEY (code, telegram_user_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS daily_activity (user_id INTEGER PRIMARY KEY, last_seen_date DATE NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS connection_settings (key TEXT PRIMARY KEY, value TEXT)')
        
        default_settings = {
            "hostname": "your.hostname.com", "ws_ports": "80, 8880, 8888, 2053",
            "ssl_port": "443", "udpcustom_port": "7300", "admin_contact": ADMIN_CONTACT_INFO,
            "payload": "your.default.payload"
        }
        for key, value in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

async def get_or_create_user(user_id, lang_code='ar', referrer_id=None, context: ContextTypes.DEFAULT_TYPE = None):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        is_new_user = not cursor.execute("SELECT 1 FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
        if is_new_user:
            today = date.today().isoformat()
            cursor.execute("INSERT INTO users (telegram_user_id, points, language_code, created_date, referrer_id) VALUES (?, ?, ?, ?, ?)", (user_id, INITIAL_POINTS, lang_code, today, referrer_id))
            conn.commit()
            if referrer_id and context:
                try:
                    cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (REFERRAL_BONUS, referrer_id))
                    conn.commit()
                    referrer_lang = get_user_lang(referrer_id)
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=get_text('referral_bonus_notification', referrer_lang).format(bonus=REFERRAL_BONUS),
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    print(f"Error awarding referral bonus to {referrer_id}: {e}")

def get_user_lang(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        res = conn.execute("SELECT language_code FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()
        return res[0] if res else 'ar'

def set_user_lang(user_id, lang_code):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE users SET language_code = ? WHERE telegram_user_id = ?", (lang_code, user_id))
        conn.commit()

def get_connection_setting(key):
    with sqlite3.connect(DB_FILE) as conn:
        result = conn.execute("SELECT value FROM connection_settings WHERE key = ?", (key,)).fetchone()
        return result[0] if result else ""

def set_connection_setting(key, value):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT OR REPLACE INTO connection_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

# =================================================================================
# 4. دوال مساعدة (Helpers)
# =================================================================================
def log_activity(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        today = date.today().isoformat()
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO daily_activity (user_id, last_seen_date) VALUES (?, ?)", (user_id, today))
            conn.commit()
        return await func(update, context, *args, **kwargs)
    return wrapper

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        channel_member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        group_member = await context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        if channel_member.status not in ['member', 'administrator', 'creator']: return False
        if group_member.status not in ['member', 'administrator', 'creator']: return False
        return True
    except Exception as e:
        print(f"Error checking membership for {user_id}: {e}")
        return False
        
# =================================================================================
# 5. أوامر البوت الأساسية
# =================================================================================
@log_activity
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user = update.effective_user
    message = update.message if not from_callback else update.callback_query.message
    
    user_lang = user.language_code
    if user_lang not in TEXTS:
        user_lang = 'ar'

    referrer_id = None
    if context.args and context.args[0].startswith('ref_'):
        try:
            referrer_id = int(context.args[0].split('_')[1])
            if referrer_id == user.id: referrer_id = None
        except (ValueError, IndexError):
            referrer_id = None

    await get_or_create_user(user.id, lang_code=user_lang, referrer_id=referrer_id, context=context)
    lang_code = get_user_lang(user.id)

    if not await check_membership(user.id, context):
        keyboard = [
            [InlineKeyboardButton(get_text('force_join_channel_button', lang_code), url=CHANNEL_LINK)],
            [InlineKeyboardButton(get_text('force_join_group_button', lang_code), url=GROUP_LINK)],
            [InlineKeyboardButton(get_text('force_join_verify_button', lang_code), callback_data='verify_join')],
        ]
        await message.reply_text(get_text('force_join_prompt', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard_layout = [
        [KeyboardButton(get_text('get_account_button', lang_code)), KeyboardButton(get_text('paid_servers_button', lang_code))],
        [KeyboardButton(get_text('balance_button', lang_code)), KeyboardButton(get_text('my_account_button', lang_code))],
        [KeyboardButton(get_text('daily_button', lang_code)), KeyboardButton(get_text('earn_points_button', lang_code))],
        [KeyboardButton(get_text('redeem_code_button', lang_code)), KeyboardButton(get_text('contact_admin_button', lang_code))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)
    await message.reply_text(get_text('welcome', lang_code), reply_markup=reply_markup)

@log_activity
async def request_new_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    
    with sqlite3.connect(DB_FILE) as conn:
        user_points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    
    if user_points < COST_PER_ACCOUNT:
        await update.message.reply_text(get_text('not_enough_points', lang_code).format(cost=COST_PER_ACCOUNT), parse_mode=ParseMode.HTML)
        return

    keyboard = [
        [InlineKeyboardButton(get_text('ssh_account_button', lang_code), callback_data='create_ssh')],
        [InlineKeyboardButton(get_text('v2ray_account_button', lang_code), callback_data='under_development')],
        [InlineKeyboardButton(get_text('udpcustom_account_button', lang_code), callback_data='under_development')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text('choose_account_type', lang_code), reply_markup=reply_markup)

async def under_development_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang_code = get_user_lang(query.from_user.id)
    await query.answer(text=get_text('under_development', lang_code), show_alert=True)

async def account_creation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    with sqlite3.connect(DB_FILE) as conn:
        user_points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    
    if user_points < COST_PER_ACCOUNT:
        await query.edit_message_text(get_text('not_enough_points', lang_code).format(cost=COST_PER_ACCOUNT), parse_mode=ParseMode.HTML)
        return

    await query.edit_message_text(text=get_text('creating_account', lang_code))

    if query.data == 'create_ssh':
        await create_ssh_account(update, context)

async def create_ssh_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    try:
        username = f"sshdatbot{user_id}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        command_to_run = ["sudo", SSH_SCRIPT_PATH, username, password, str(SSH_ACCOUNT_EXPIRY_DAYS)]

        process = subprocess.run(command_to_run, capture_output=True, text=True, timeout=30, check=True)
        
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE users SET points = points - ? WHERE telegram_user_id = ?", (COST_PER_ACCOUNT, user_id))
            conn.execute("INSERT INTO ssh_accounts (telegram_user_id, ssh_username, ssh_password, created_at) VALUES (?, ?, ?, ?)", (user_id, username, password, datetime.now()))
            conn.commit()

        hostname = get_connection_setting("hostname")
        ws_ports = get_connection_setting("ws_ports")
        ssl_port = get_connection_setting("ssl_port")
        udpcustom_port = get_connection_setting("udpcustom_port")
        payload_template = get_connection_setting("payload")
        
        try:
            expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, stderr=subprocess.DEVNULL)
            expiry_line = next((line for line in expiry_output.split('\n') if "Account expires" in line), None)
            expiry = expiry_line.split(':', 1)[1].strip() if expiry_line else "N/A"
        except Exception:
            expiry = "N/A"

        account_info = get_text('account_details_full', lang_code).format(
            username=html.escape(username), password=html.escape(password), expiry=html.escape(expiry),
            hostname=html.escape(hostname), ws_ports=html.escape(ws_ports),
            ssl_port=html.escape(ssl_port), udpcustom_port=html.escape(udpcustom_port),
            payload=html.escape(payload_template)
        )
        await query.edit_message_text(account_info, parse_mode=ParseMode.HTML)

    except Exception as e:
        print(f"SSH Creation Error: {e}"); traceback.print_exc()
        await query.edit_message_text(get_text('creation_error', lang_code))

@log_activity
async def my_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    
    response_parts = []
    
    with sqlite3.connect(DB_FILE) as conn:
        ssh_accounts = conn.execute("SELECT ssh_username, ssh_password FROM ssh_accounts WHERE telegram_user_id = ?", (user_id,)).fetchall()

    if ssh_accounts:
        response_parts.append(get_text('your_accounts', lang_code))
        hostname = get_connection_setting("hostname")
        ws_ports = get_connection_setting("ws_ports")
        ssl_port = get_connection_setting("ssl_port")
        udpcustom_port = get_connection_setting("udpcustom_port")
        payload_template = get_connection_setting("payload")
        for username, password in ssh_accounts:
            try:
                expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, stderr=subprocess.DEVNULL)
                expiry_line = next((line for line in expiry_output.split('\n') if "Account expires" in line), None)
                expiry = expiry_line.split(':', 1)[1].strip() if expiry_line else "N/A"
            except Exception:
                expiry = "N/A"
            response_parts.append(get_text('account_details_full', lang_code).format(
                username=html.escape(username), password=html.escape(password), expiry=html.escape(expiry),
                hostname=html.escape(hostname), ws_ports=html.escape(ws_ports),
                ssl_port=html.escape(ssl_port), udpcustom_port=html.escape(udpcustom_port),
                payload=html.escape(payload_template)
            ))

    if not response_parts:
        await update.message.reply_text(get_text('no_accounts_found', lang_code))
        return

    full_response = "\n\n---\n\n".join(response_parts)
    await update.message.reply_text(full_response, parse_mode=ParseMode.HTML)

@log_activity
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        points = conn.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
    await update.message.reply_text(get_text('balance_info', lang_code).format(points=points), parse_mode=ParseMode.HTML)

@log_activity
async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        today = date.today()
        last_claim_str = cursor.execute("SELECT last_daily_claim FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        
        if last_claim_str and date.fromisoformat(last_claim_str) >= today:
            await update.message.reply_text(get_text('daily_bonus_already_claimed', lang_code)); return
            
        cursor.execute("UPDATE users SET points = points + ?, last_daily_claim = ? WHERE telegram_user_id = ?", (DAILY_LOGIN_BONUS, today.isoformat(), user_id))
        conn.commit()
        new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        await update.message.reply_text(get_text('daily_bonus_claimed', lang_code).format(bonus=DAILY_LOGIN_BONUS, new_balance=new_balance), parse_mode=ParseMode.HTML)

@log_activity
async def earn_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    with sqlite3.connect(DB_FILE) as conn:
        all_channels = conn.execute("SELECT channel_id, channel_link, reward_points, channel_name FROM reward_channels").fetchall()
        claimed_ids = {row[0] for row in conn.execute("SELECT channel_id FROM user_channel_rewards WHERE telegram_user_id = ?", (user_id,))}
    
    keyboard = []
    for cid, link, points, name in all_channels:
        if cid in claimed_ids:
            button_text = f"✅ {name}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data="dummy")])
        else:
            button_text = f"{name} (+{points} {get_text('points', lang_code)})"
            keyboard.append([InlineKeyboardButton(button_text, url=link)])
            keyboard.append([InlineKeyboardButton(get_text('verify_join_button', lang_code), callback_data=f"verify_r_{cid}_{points}")])
    
    if all_channels:
        keyboard.append([InlineKeyboardButton("-----------", callback_data="dummy")])
    keyboard.append([InlineKeyboardButton(get_text('referral_button', lang_code), callback_data='get_referral_link')])

    if from_callback:
        reply_func = update.callback_query.edit_message_text
    else:
        reply_func = update.message.reply_text
    
    await reply_func(get_text('rewards_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

@log_activity
async def contact_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    contact_info = get_connection_setting("admin_contact")
    await update.message.reply_text(get_text('contact_admin_info', lang_code).format(contact_info=contact_info))

@log_activity
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en')],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data='set_lang_ar')],
    ]
    await update.message.reply_text(get_text('choose_language', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = query.data.split('_')[-1]
    set_user_lang(user_id, lang_code)
    lang_map = {'en': 'English', 'ar': 'العربية'}
    await query.edit_message_text(text=get_text('language_set', lang_code).format(lang_name=lang_map.get(lang_code)))
    await start(update, context, from_callback=True)

# =================================================================================
# 6. قسم الدفع (Payment Section)
# =================================================================================
@log_activity
async def paid_servers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)

    keyboard = [
        [InlineKeyboardButton(get_text('paypal_button', lang_code), callback_data='pay_paypal')],
        [InlineKeyboardButton(get_text('telegram_stars_button', lang_code), callback_data='pay_stars')],
        [InlineKeyboardButton(get_text('moroccan_bank_button', lang_code), callback_data='pay_bank_transfer')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text('choose_payment_method', lang_code), reply_markup=reply_markup)

async def bank_transfer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)
    await query.message.reply_text(
        get_text('bank_transfer_details', lang_code),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def paypal_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    if not PAYPAL_PROVIDER_TOKEN or "YOUR_" in PAYPAL_PROVIDER_TOKEN:
        await context.bot.send_message(chat_id, get_text('payment_not_configured', lang_code))
        return

    title = get_text('payment_invoice_title', lang_code)
    description = get_text('payment_invoice_description', lang_code)
    payload = f"PAID_SSH_PAYPAL_{user_id}_{uuid.uuid4()}"
    prices = PAYPAL_PAYMENT_OPTIONS

    await context.bot.send_invoice(
        chat_id, title, description, payload, PAYPAL_PROVIDER_TOKEN, PAYMENT_CURRENCY, prices
    )

async def stars_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    title = get_text('payment_invoice_title', lang_code)
    description = get_text('payment_invoice_description', lang_code)
    payload = f"PAID_SSH_STARS_{user_id}_{uuid.uuid4()}"
    currency = "XTR"
    prices = STARS_PAYMENT_OPTIONS

    try:
        await context.bot.send_invoice(
            chat_id, title, description, payload, None, currency, prices
        )
    except BadRequest as e:
        print(f"Error sending Stars invoice: {e}")
        await context.bot.send_message(chat_id, get_text('payment_not_configured', lang_code))

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    # يمكنك هنا التحقق من صحة الطلب، لكننا سنوافق على الكل
    await query.answer(ok=True)

async def create_paid_ssh_user(user_id: int, expiry_days: int):
    username = f"paid{user_id}{random.randint(100, 999)}"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    command_to_run = ["sudo", SSH_SCRIPT_PATH, username, password, str(expiry_days)]

    process = subprocess.run(command_to_run, capture_output=True, text=True, timeout=30, check=True)

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO ssh_accounts (telegram_user_id, ssh_username, ssh_password, created_at) VALUES (?, ?, ?, ?)",
                     (user_id, username, password, datetime.now()))
        conn.commit()

    try:
        expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, stderr=subprocess.DEVNULL)
        expiry_line = next((line for line in expiry_output.split('\n') if "Account expires" in line), None)
        expiry = expiry_line.split(':', 1)[1].strip() if expiry_line else f"{expiry_days} days from now"
    except Exception:
        expiry = f"{expiry_days} days from now"

    return username, password, expiry

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)

    try:
        username, password, expiry_date = await create_paid_ssh_user(user_id, PAID_SSH_ACCOUNT_EXPIRY_DAYS)

        hostname = get_connection_setting("hostname")
        ws_ports = get_connection_setting("ws_ports")
        ssl_port = get_connection_setting("ssl_port")
        udpcustom_port = get_connection_setting("udpcustom_port")
        payload = get_connection_setting("payload")

        account_info = get_text('account_details_full', lang_code).format(
            username=html.escape(username), password=html.escape(password), expiry=html.escape(expiry_date),
            hostname=html.escape(hostname), ws_ports=html.escape(ws_ports),
            ssl_port=html.escape(ssl_port), udpcustom_port=html.escape(udpcustom_port),
            payload=html.escape(payload)
        )
        await update.message.reply_text(
            f"{get_text('payment_successful_creation', lang_code)}\n\n{account_info}",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        print(f"Paid SSH Creation Error after payment: {e}"); traceback.print_exc()
        await update.message.reply_text(get_text('creation_error', lang_code))


# =================================================================================
# 7. Admin Panel & Features
# =================================================================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID: return
    lang_code = get_user_lang(user_id)
    keyboard = [
        [InlineKeyboardButton(get_text('admin_manage_rewards_button', lang_code), callback_data='admin_manage_rewards')],
        [InlineKeyboardButton(get_text('admin_manage_codes_button', lang_code), callback_data='admin_manage_codes')],
        [InlineKeyboardButton(get_text('admin_user_stats_button', lang_code), callback_data='admin_user_stats')],
        [InlineKeyboardButton(get_text('admin_edit_connection_info_button', lang_code), callback_data='admin_edit_connection_info')],
    ]
    await update.message.reply_text(get_text('admin_panel_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    with sqlite3.connect(DB_FILE) as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        active_today = conn.execute("SELECT COUNT(*) FROM daily_activity WHERE last_seen_date = ?", (today,)).fetchone()[0]
        active_yesterday = conn.execute("SELECT COUNT(*) FROM daily_activity WHERE last_seen_date = ?", (yesterday,)).fetchone()[0]
        new_today = conn.execute("SELECT COUNT(*) FROM users WHERE created_date = ?", (today,)).fetchone()[0]
    
    stats_text = get_text('user_stats_info', lang_code).format(
        total_users=total_users,
        active_today=active_today,
        active_yesterday=active_yesterday,
        new_today=new_today
    )
    keyboard = [[InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_panel_main')]]
    await query.edit_message_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_USER_ID: return
    
    data = query.data
    lang_code = get_user_lang(user_id)
    
    if data == 'admin_panel_main':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_manage_rewards_button', lang_code), callback_data='admin_manage_rewards')],
            [InlineKeyboardButton(get_text('admin_manage_codes_button', lang_code), callback_data='admin_manage_codes')],
            [InlineKeyboardButton(get_text('admin_user_stats_button', lang_code), callback_data='admin_user_stats')],
            [InlineKeyboardButton(get_text('admin_edit_connection_info_button', lang_code), callback_data='admin_edit_connection_info')],
        ]
        await query.edit_message_text(get_text('admin_panel_header', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_manage_rewards':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_add_channel_button', lang_code), callback_data='admin_add_channel_start')],
            [InlineKeyboardButton(get_text('admin_remove_channel_button', lang_code), callback_data='admin_remove_channel_start')],
            [InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_panel_main')]
        ]
        await query.edit_message_text(get_text('admin_manage_rewards_button', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_manage_codes':
        keyboard = [
            [InlineKeyboardButton(get_text('admin_create_code_button', lang_code), callback_data='admin_create_code_start')],
            [InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_panel_main')]
        ]
        await query.edit_message_text(get_text('admin_manage_codes_button', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == 'admin_user_stats':
        await show_user_stats(update, context)

async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    await query.edit_message_text(get_text('admin_add_channel_name_prompt', lang_code))
    return ADD_CHANNEL_NAME

async def add_channel_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_name'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_add_channel_link_prompt', lang_code))
    return ADD_CHANNEL_LINK

async def add_channel_get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['channel_link'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_add_channel_id_prompt', lang_code))
    return ADD_CHANNEL_ID

async def add_channel_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    try:
        context.user_data['channel_id'] = int(update.message.text)
        await update.message.reply_text(get_text('admin_add_channel_points_prompt', lang_code))
        return ADD_CHANNEL_POINTS
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code)); return ADD_CHANNEL_ID

async def add_channel_get_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    try:
        points = int(update.message.text)
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO reward_channels (channel_id, channel_link, reward_points, channel_name) VALUES (?, ?, ?, ?)",
                         (context.user_data['channel_id'], context.user_data['channel_link'], points, context.user_data['channel_name']))
        await update.message.reply_text(get_text('admin_channel_added_success', lang_code))
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code)); return ADD_CHANNEL_POINTS

async def remove_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    with sqlite3.connect(DB_FILE) as conn:
        channels = conn.execute("SELECT channel_id, channel_name FROM reward_channels").fetchall()
    if not channels:
        await query.edit_message_text(get_text('no_channels_available', lang_code), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_manage_rewards')]])); return
    keyboard = [[InlineKeyboardButton(name, callback_data=f"remove_c_{cid}")] for cid, name in channels]
    keyboard.append([InlineKeyboardButton(get_text('admin_return_button', lang_code), callback_data='admin_manage_rewards')])
    await query.edit_message_text(get_text('admin_remove_channel_prompt', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

async def remove_channel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    channel_id = int(query.data.split('_')[-1])
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM reward_channels WHERE channel_id = ?", (channel_id,))
        conn.execute("DELETE FROM user_channel_rewards WHERE channel_id = ?", (channel_id,))
    await query.edit_message_text(get_text('admin_channel_removed_success', lang_code))
    await remove_channel_start(update, context)

async def create_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    await query.edit_message_text(get_text('admin_create_code_prompt_name', lang_code))
    return CREATE_CODE_NAME

async def receive_code_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['code_name'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_create_code_prompt_points', lang_code))
    return CREATE_CODE_POINTS

async def receive_code_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    try:
        context.user_data['code_points'] = int(update.message.text)
        await update.message.reply_text(get_text('admin_create_code_prompt_uses', lang_code))
        return CREATE_CODE_USES
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code)); return CREATE_CODE_POINTS

async def receive_code_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    try:
        uses = int(update.message.text)
        name = context.user_data['code_name']
        points = context.user_data['code_points']
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT OR REPLACE INTO redeem_codes (code, points, max_uses, current_uses) VALUES (?, ?, ?, 0)", (name, points, uses))
        await update.message.reply_text(get_text('admin_code_created', lang_code).format(code=name, points=points, uses=uses), parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code)); return CREATE_CODE_USES

async def edit_connection_info_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    await query.edit_message_text(get_text('admin_edit_hostname_prompt', lang_code))
    return EDIT_HOSTNAME

async def edit_hostname_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hostname'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_ws_ports_prompt', lang_code))
    return EDIT_WS_PORTS

async def edit_ws_ports_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ws_ports'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_ssl_port_prompt', lang_code))
    return EDIT_SSL_PORT

async def edit_ssl_port_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ssl_port'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_udpcustom_prompt', lang_code))
    return EDIT_UDPCUSTOM

async def edit_udpcustom_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['udpcustom_port'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_contact_prompt', lang_code))
    return EDIT_ADMIN_CONTACT

async def edit_admin_contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['admin_contact'] = update.message.text
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('admin_edit_payload_prompt', lang_code))
    return EDIT_PAYLOAD

async def edit_payload_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    set_connection_setting('hostname', context.user_data['hostname'])
    set_connection_setting('ws_ports', context.user_data['ws_ports'])
    set_connection_setting('ssl_port', context.user_data['ssl_port'])
    set_connection_setting('udpcustom_port', context.user_data['udpcustom_port'])
    set_connection_setting('admin_contact', context.user_data['admin_contact'])
    set_connection_setting('payload', update.message.text)
    await update.message.reply_text(get_text('admin_info_updated_success', lang_code))
    context.user_data.clear()
    return ConversationHandler.END

@log_activity
async def redeem_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('redeem_prompt', lang_code))
    return REDEEM_CODE_INPUT

async def redeem_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_code = get_user_lang(user_id)
    code = update.message.text
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        code_data = cursor.execute("SELECT points, max_uses, current_uses FROM redeem_codes WHERE code = ?", (code,)).fetchone()
        
        if not code_data:
            await update.message.reply_text(get_text('redeem_invalid_code', lang_code)); return ConversationHandler.END
        
        points, max_uses, current_uses = code_data
        if current_uses >= max_uses:
            await update.message.reply_text(get_text('redeem_limit_reached', lang_code)); return ConversationHandler.END
        
        if cursor.execute("SELECT 1 FROM redeemed_users WHERE code = ? AND telegram_user_id = ?", (code, user_id)).fetchone():
            await update.message.reply_text(get_text('redeem_already_used', lang_code)); return ConversationHandler.END
            
        cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points, user_id))
        cursor.execute("UPDATE redeem_codes SET current_uses = current_uses + 1 WHERE code = ?", (code,))
        cursor.execute("INSERT INTO redeemed_users (code, telegram_user_id) VALUES (?, ?)", (code, user_id))
        new_balance = cursor.execute("SELECT points FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
        await update.message.reply_text(get_text('redeem_success', lang_code).format(points=points, new_balance=new_balance), parse_mode=ParseMode.HTML)
    return ConversationHandler.END

async def get_referral_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    message_text = get_text('referral_info', lang_code).format(
        bonus=REFERRAL_BONUS,
        link=referral_link
    )
    await query.message.reply_text(message_text, parse_mode=ParseMode.HTML)

async def verify_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    if await check_membership(user_id, context):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            claimed = cursor.execute("SELECT join_bonus_claimed FROM users WHERE telegram_user_id = ?", (user_id,)).fetchone()[0]
            if not claimed:
                cursor.execute("UPDATE users SET points = points + ?, join_bonus_claimed = 1 WHERE telegram_user_id = ?", (JOIN_BONUS, user_id))
                conn.commit()
                if JOIN_BONUS > 0:
                    await query.answer(get_text('join_bonus_awarded', lang_code).format(bonus=JOIN_BONUS), show_alert=True)
            
        await query.edit_message_text(get_text('force_join_success', lang_code))
        await start(update, context, from_callback=True)
    else:
        await query.answer(get_text('force_join_fail', lang_code), show_alert=True)

async def verify_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)
    
    try:
        _, _, channel_id_str, points_str = query.data.split('_')
        channel_id, points = int(channel_id_str), int(points_str)
    except (ValueError, IndexError):
        await query.answer("Data error.", show_alert=True); return

    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await query.answer(get_text('reward_fail', lang_code), show_alert=True); return
    except Exception as e:
        await query.answer(f"Error: Could not verify. Make sure the bot is an admin in the channel.", show_alert=True); return
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if cursor.execute("SELECT 1 FROM user_channel_rewards WHERE telegram_user_id = ? AND channel_id = ?", (user_id, channel_id)).fetchone():
            await query.answer("You have already claimed this reward.", show_alert=True); return
        
        cursor.execute("UPDATE users SET points = points + ? WHERE telegram_user_id = ?", (points, user_id))
        cursor.execute("INSERT INTO user_channel_rewards (telegram_user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
        conn.commit()
    
    await query.answer(get_text('reward_success', lang_code).format(points=points), show_alert=True)
    await earn_points_command(update, context, from_callback=True)

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    await update.message.reply_text(get_text('operation_cancelled', lang_code))
    context.user_data.clear()
    return ConversationHandler.END

# =================================================================================
# 9. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    init_db()
    
    if "YOUR_TELEGRAM_BOT_TOKEN" in TOKEN:
        print("FATAL ERROR: Bot token is not set.")
        sys.exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    
    conv_defaults = {'per_user': True, 'per_message': False, 'allow_reentry': True}

    edit_info_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_connection_info_start, pattern='^admin_edit_connection_info$')],
        states={
            EDIT_HOSTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_hostname_received)],
            EDIT_WS_PORTS: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_ws_ports_received)],
            EDIT_SSL_PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_ssl_port_received)],
            EDIT_UDPCUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_udpcustom_received)],
            EDIT_ADMIN_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_admin_contact_received)],
            EDIT_PAYLOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, edit_payload_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_channel_start, pattern='^admin_add_channel_start$')],
        states={
            ADD_CHANNEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_channel_get_name)],
            ADD_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_channel_get_link)],
            ADD_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_channel_get_id)],
            ADD_CHANNEL_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_channel_get_points)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    create_code_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_code_start, pattern='^admin_create_code_start$')],
        states={
            CREATE_CODE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_code_name)],
            CREATE_CODE_POINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_code_points)],
            CREATE_CODE_USES: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_code_uses)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )
    
    def create_lang_regex(key):
        texts = [re.escape(get_text(key, lang)) for lang in TEXTS.keys()]
        return f"^({'|'.join(texts)})$"

    redeem_code_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(create_lang_regex('redeem_code_button')) & filters.ChatType.PRIVATE, redeem_code_start)],
        states={REDEEM_CODE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, redeem_code_received)]},
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
        **conv_defaults
    )

    app.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("admin", admin_panel, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("language", language_command, filters=filters.ChatType.PRIVATE))

    app.add_handler(add_channel_conv)
    app.add_handler(create_code_conv)
    app.add_handler(redeem_code_conv)
    app.add_handler(edit_info_conv)

    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('get_account_button')) & filters.ChatType.PRIVATE, request_new_account))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('my_account_button')) & filters.ChatType.PRIVATE, my_accounts))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('balance_button')) & filters.ChatType.PRIVATE, balance_command))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('daily_button')) & filters.ChatType.PRIVATE, daily_command))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('earn_points_button')) & filters.ChatType.PRIVATE, earn_points_command))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('contact_admin_button')) & filters.ChatType.PRIVATE, contact_admin_command))
    app.add_handler(MessageHandler(filters.Regex(create_lang_regex('paid_servers_button')) & filters.ChatType.PRIVATE, paid_servers_command))
    
    app.add_handler(CallbackQueryHandler(account_creation_callback, pattern='^create_ssh$'))
    app.add_handler(CallbackQueryHandler(under_development_callback, pattern='^under_development$'))
    app.add_handler(CallbackQueryHandler(verify_join_callback, pattern='^verify_join$'))
    app.add_handler(CallbackQueryHandler(verify_reward_callback, pattern='^verify_r_'))
    app.add_handler(CallbackQueryHandler(remove_channel_confirm, pattern='^remove_c_'))
    app.add_handler(CallbackQueryHandler(set_language_callback, pattern='^set_lang_'))
    app.add_handler(CallbackQueryHandler(get_referral_link_callback, pattern='^get_referral_link$'))
    app.add_handler(CallbackQueryHandler(bank_transfer_callback, pattern='^pay_bank_transfer$'))
    app.add_handler(CallbackQueryHandler(paypal_payment_callback, pattern='^pay_paypal$'))
    app.add_handler(CallbackQueryHandler(stars_payment_callback, pattern='^pay_stars$'))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), pattern='^dummy$'))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern='^admin_'))
    
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT & filters.ChatType.PRIVATE, successful_payment_callback))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
