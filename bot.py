import sys
import sqlite3
import re
import html
import random
from datetime import datetime, date, timedelta

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.constants import ParseMode

# --- استيراد من الملفات المنفصلة ---
import vps_manager
from payments import register_payment_handlers
from bot_config import * # استيراد جميع الإعدادات
from bot_utils import * # استيراد جميع الدوال المساعدة والنصوص

# =================================================================================
#  Conversation handler states (تبقى هنا لأنها مرتبطة بالمعالجات في هذا الملف)
# =================================================================================
(ADD_CHANNEL_NAME, ADD_CHANNEL_LINK, ADD_CHANNEL_ID, ADD_CHANNEL_POINTS) = range(4)
(CREATE_CODE_NAME, CREATE_CODE_POINTS, CREATE_CODE_USES) = range(4, 7)
(REDEEM_CODE_INPUT,) = range(7, 8)
(EDIT_HOSTNAME, EDIT_WS_PORTS, EDIT_SSL_PORT, EDIT_UDPCUSTOM, EDIT_ADMIN_CONTACT, EDIT_PAYLOAD) = range(8, 14)
(GRANT_USER_ID,) = range(14, 15)

# =================================================================================
# 3. إدارة قاعدة البيانات والمستخدمين
# =================================================================================
def init_db():
    # ... (كود init_db يبقى كما هو) ...

async def get_or_create_user(user_id, lang_code='ar', referrer_id=None, context: ContextTypes.DEFAULT_TYPE = None):
    # ... (كود get_or_create_user يبقى كما هو) ...

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    # ... (كود check_membership يبقى كما هو) ...

# =================================================================================
# 5. أوامر البوت الأساسية
# =================================================================================
@log_activity
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    # ... (كود start يبقى كما هو) ...

@log_activity
async def request_new_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (كود request_new_account يبقى كما هو) ...

async def under_development_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (كود under_development_callback يبقى كما هو) ...

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
        username = f"sshdatbot{user_id}"
        # --- استدعاء مدير السيرفر ---
        created_user, password = vps_manager.create_ssh_user(user_id, username, SSH_ACCOUNT_EXPIRY_DAYS)
        
        if created_user and password:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET points = points - ? WHERE telegram_user_id = ?", (COST_PER_ACCOUNT, user_id))
                conn.commit()
            
            expiry_date = vps_manager.get_user_expiry(created_user)
            account_info = get_text('account_details_full', lang_code).format(
                username=html.escape(created_user), password=html.escape(password), expiry=html.escape(expiry_date),
                hostname=html.escape(get_connection_setting("hostname")), ws_ports=html.escape(get_connection_setting("ws_ports")),
                ssl_port=html.escape(get_connection_setting("ssl_port")), udpcustom_port=html.escape(get_connection_setting("udpcustom_port")),
                payload=html.escape(get_connection_setting("payload")))
            await query.edit_message_text(account_info, parse_mode=ParseMode.HTML)
        else:
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
        for username, password in ssh_accounts:
            # --- استدعاء مدير السيرفر ---
            expiry = vps_manager.get_user_expiry(username)
            response_parts.append(get_text('account_details_full', lang_code).format(
                username=html.escape(username), password=html.escape(password), expiry=html.escape(expiry),
                hostname=html.escape(get_connection_setting("hostname")), ws_ports=html.escape(get_connection_setting("ws_ports")),
                ssl_port=html.escape(get_connection_setting("ssl_port")), udpcustom_port=html.escape(get_connection_setting("udpcustom_port")),
                payload=html.escape(get_connection_setting("payload"))))
    
    if not response_parts:
        await update.message.reply_text(get_text('no_accounts_found', lang_code))
        return

    await update.message.reply_text("\n\n---\n\n".join(response_parts), parse_mode=ParseMode.HTML)

# ... (باقي الدوال مثل balance_command, daily_command, earn_points_command, إلخ، تبقى كما هي) ...

# =================================================================================
# 7. Admin Panel & Features
# =================================================================================
# ... (كل دوال لوحة التحكم تبقى كما هي، لكن سنعدل دالة المنح) ...

async def receive_user_id_for_grant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    lang_code = get_user_lang(admin_id)
    
    try:
        user_id_to_grant = int(update.message.text)
    except ValueError:
        await update.message.reply_text(get_text('invalid_input', lang_code))
        return GRANT_USER_ID

    username_prefix = f"paid{user_id_to_grant}{random.randint(100, 999)}"
    # --- استدعاء مدير السيرفر ---
    username, password = vps_manager.create_ssh_user(user_id_to_grant, username_prefix, PAID_SSH_ACCOUNT_EXPIRY_DAYS)

    if username and password:
        expiry_date = vps_manager.get_user_expiry(username)
        target_user_lang = get_user_lang(user_id_to_grant)
        account_info = get_text('account_details_full', target_user_lang).format(
            username=html.escape(username), password=html.escape(password), expiry=html.escape(expiry_date),
            hostname=html.escape(get_connection_setting("hostname")), ws_ports=html.escape(get_connection_setting("ws_ports")),
            ssl_port=html.escape(get_connection_setting("ssl_port")), udpcustom_port=html.escape(get_connection_setting("udpcustom_port")),
            payload=html.escape(get_connection_setting("payload")))
        
        await context.bot.send_message(chat_id=user_id_to_grant, text=get_text('admin_grant_notification_to_user', target_user_lang))
        await context.bot.send_message(chat_id=user_id_to_grant, text=account_info, parse_mode=ParseMode.HTML)
        await update.message.reply_text(get_text('admin_grant_success_to_admin', lang_code).format(user_id=user_id_to_grant), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(get_text('admin_grant_fail_to_admin', lang_code))
        
    return ConversationHandler.END

# ... (باقي دوال لوحة التحكم ودوال ردود الأفعال مثل redeem_code, verify_join تبقى كما هي) ...

# =================================================================================
# 9. نقطة انطلاق البوت (Main Entry Point)
# =================================================================================
def main():
    init_db()
    
    if "YOUR_TELEGRAM_BOT_TOKEN" in TOKEN:
        print("FATAL ERROR: Bot token is not set.")
        sys.exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    
    # ... (كل كود إضافة المعالجات والمحادثات يبقى كما هو) ...
    # مثال: app.add_handler(CommandHandler("start", start))
    #       app.add_handler(add_channel_conv)
    
    # --- حذف كل ما يتعلق بالمدفوعات من هنا ---

    # --- تسجيل معالجات الدفع من ملفها الخاص ---
    register_payment_handlers(app)

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
