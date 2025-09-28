import html
import uuid
import asyncio
import threading
from flask import Flask, request, jsonify
import paypalrestsdk

from telegram import Update, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import BadRequest

# --- استيراد من الملفات الأخرى ---
import vps_manager
from bot_config import (
    PAYPAL_MODE, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_PRICE,
    PAYPAL_CURRENCY, STARS_PAYMENT_OPTIONS, PAID_SSH_ACCOUNT_EXPIRY_DAYS, CHANNEL_LINK, GROUP_LINK
)
from bot_utils import get_user_lang, get_text, get_connection_setting, log_activity

# =================================================================================
# 1. عرض خيارات الدفع
# =================================================================================
@log_activity
async def paid_servers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = get_user_lang(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton(get_text('paypal_button', lang_code), callback_data='pay_paypal')],
        [InlineKeyboardButton(get_text('telegram_stars_button', lang_code), callback_data='pay_stars')],
        [InlineKeyboardButton(get_text('moroccan_bank_button', lang_code), callback_data='pay_bank_transfer')],
    ]
    await update.message.reply_text(get_text('choose_payment_method', lang_code), reply_markup=InlineKeyboardMarkup(keyboard))

# =================================================================================
# 2. معالجة طرق الدفع المختلفة
# =================================================================================
async def bank_transfer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(get_text('bank_transfer_details', get_user_lang(query.from_user.id)), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def paypal_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = get_user_lang(user_id)

    if "YOUR_PAYPAL_CLIENT_ID" in PAYPAL_CLIENT_ID:
        await query.message.reply_text(get_text('payment_not_configured', lang_code))
        return

    paypalrestsdk.configure({"mode": PAYPAL_MODE, "client_id": PAYPAL_CLIENT_ID, "client_secret": PAYPAL_CLIENT_SECRET})
    invoice_id = f"SSH-{user_id}-{uuid.uuid4().hex[:8]}"

    payment = paypalrestsdk.Payment({
        "intent": "sale", "payer": {"payment_method": "paypal"},
        "redirect_urls": {"return_url": f"https://t.me/{CHANNEL_LINK.split('/')[-1]}", "cancel_url": f"https://t.me/{GROUP_LINK.split('/')[-1]}"},
        "transactions": [{"item_list": {"items": [{"name": get_text('payment_invoice_title', lang_code), "sku": "PAID_SSH_30_DAYS", "price": PAYPAL_PRICE, "currency": PAYPAL_CURRENCY, "quantity": 1}]},
                          "amount": {"total": PAYPAL_PRICE, "currency": PAYPAL_CURRENCY},
                          "description": get_text('payment_invoice_description', lang_code), "invoice_number": invoice_id}]})

    if payment.create():
        approval_link = next(link.href for link in payment.links if link.rel == "approval_url")
        message_text = (f"✅ رابط الدفع جاهز.\n\n"
                        f"🔗 <a href='{approval_link}'><b>اضغط هنا لإتمام الدفع</b></a>\n\n"
                        f"⚠️ سيتم إنشاء حسابك تلقائيًا فور إتمام الدفع.")
        await query.message.reply_text(message_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        print(f"PayPal Error: {payment.error}")
        await query.message.reply_text("❌ حدث خطأ أثناء إنشاء رابط الدفع.")

async def stars_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = get_user_lang(query.from_user.id)
    payload = f"PAID_SSH_STARS_{query.from_user.id}_{uuid.uuid4()}"
    try:
        await context.bot.send_invoice(query.message.chat_id, get_text('payment_invoice_title', lang_code),
                                       get_text('payment_invoice_description', lang_code), payload, None, "XTR", STARS_PAYMENT_OPTIONS)
    except BadRequest as e:
        print(f"Error sending Stars invoice: {e}")
        await context.bot.send_message(query.message.chat_id, get_text('payment_not_configured', lang_code))

# =================================================================================
# 3. معالجة الدفع الناجح وإنشاء الحساب
# =================================================================================
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await create_and_send_paid_account(update.effective_user.id, context.application)

async def create_and_send_paid_account(user_id: int, application):
    lang_code = get_user_lang(user_id)
    username_prefix = f"paid{user_id}{random.randint(100, 999)}"
    
    username, password = vps_manager.create_ssh_user(user_id, username_prefix, PAID_SSH_ACCOUNT_EXPIRY_DAYS)
    
    if username and password:
        expiry_date = vps_manager.get_user_expiry(username)
        account_info = get_text('account_details_full', lang_code).format(
            username=html.escape(username), password=html.escape(password), expiry=html.escape(expiry_date),
            hostname=html.escape(get_connection_setting("hostname")), ws_ports=html.escape(get_connection_setting("ws_ports")),
            ssl_port=html.escape(get_connection_setting("ssl_port")), udpcustom_port=html.escape(get_connection_setting("udpcustom_port")),
            payload=html.escape(get_connection_setting("payload")))
        
        await application.bot.send_message(chat_id=user_id, text=f"{get_text('payment_successful_creation', lang_code)}\n\n{account_info}", parse_mode=ParseMode.HTML)
    else:
        await application.bot.send_message(chat_id=user_id, text=get_text('creation_error', lang_code))

# =================================================================================
# 4. Webhook Handler for PayPal
# =================================================================================
def setup_webhook_server(application):
    flask_app = Flask(__name__)
    @flask_app.route('/paypal-webhook', methods=['POST'])
    def paypal_webhook():
        data = request.json
        if data.get('event_type') == 'PAYMENTS.SALE.COMPLETED':
            try:
                invoice_id = data['resource']['invoice_number']
                if invoice_id.startswith('SSH-'):
                    user_id = int(invoice_id.split('-')[1])
                    print(f"Webhook: Payment successful for user_id: {user_id}")
                    asyncio.run_coroutine_threadsafe(create_and_send_paid_account(user_id, application), application.loop)
            except Exception as e:
                print(f"Webhook Error: Could not process data: {e}")
        return jsonify({'status': 'success'}), 200
    return flask_app

def run_flask_app(app):
    app.run(host='0.0.0.0', port=8000, debug=False)

# =================================================================================
# 5. تسجيل كل معالجات الدفع
# =================================================================================
def register_payment_handlers(application):
    application.add_handler(MessageHandler(filters.Regex(r'💳.*'), paid_servers_command))
    application.add_handler(CallbackQueryHandler(bank_transfer_callback, pattern='^pay_bank_transfer$'))
    application.add_handler(CallbackQueryHandler(paypal_payment_callback, pattern='^pay_paypal$'))
    application.add_handler(CallbackQueryHandler(stars_payment_callback, pattern='^pay_stars$'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT & filters.ChatType.PRIVATE, successful_payment_callback_telegram))

    flask_app = setup_webhook_server(application)
    threading.Thread(target=run_flask_app, args=(flask_app,), daemon=True).start()
    print("Payment webhook server is running...")
