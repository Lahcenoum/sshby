from telegram import LabeledPrice

# =================================================================================
# 1. الإعدادات الرئيسية (Configuration)
# =================================================================================
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_USER_ID = 5344028088 # استبدل هذا بالمعرف الخاص بك
ADMIN_CONTACT_INFO = "@YourAdminUsername" # استبدل هذا باسم المستخدم الخاص بك
DB_FILE = 'ssh_bot_users.db'

# --- إعدادات الدفع (Payment Settings) ---
PAYPAL_MODE = "sandbox"  # سيتم تعديله إلى "live" في الإنتاج
PAYPAL_CLIENT_ID = "YOUR_PAYPAL_CLIENT_ID"  # سيتم إدخاله بواسطة سكربت التثبيت
PAYPAL_CLIENT_SECRET = "YOUR_PAYPAL_CLIENT_SECRET" # سيتم إدخاله بواسطة سكربت التثبيت
PAYPAL_PRICE = "2.40" # السعر المحدد للدفع عبر باي بال
PAYPAL_CURRENCY = "USD"
STARS_PAYMENT_OPTIONS = [LabeledPrice(label="سيرفر مدفوع (30 يوم)", amount=1050)]

# --- إعدادات SSH ---
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
        "admin_grant_account_button": "🚀 منح حساب مدفوع",
        "admin_grant_account_prompt": "أرسل ID المستخدم الذي تريد منحه حسابًا مدفوعًا (30 يومًا):",
        "admin_grant_success_to_admin": "✅ تم إنشاء وإرسال الحساب المدفوع بنجاح للمستخدم صاحب الـ ID: <code>{user_id}</code>",
        "admin_grant_fail_to_admin": "❌ فشل إنشاء أو إرسال الحساب. تأكد من أن الـ ID صحيح وأن المستخدم قد بدأ البوت من قبل.",
        "admin_grant_notification_to_user": "🎉 تهانينا! لقد قام الأدمن بتفعيل حسابك المدفوع. إليك التفاصيل:",
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
        "paypal_button": "💳 الدفع عبر PayPal",
        "telegram_stars_button": "⭐ نجوم تليجرام",
        "moroccan_bank_button": "🏦 تحويل مغربي",
        "bank_transfer_details": """
<b>للدفع عبر تحويل مغربي:</b>

المرجو تحويل مبلغ <b>25 درهم مغربي</b> إلى أحد الحسابات التالية:

<b>التجاري وفاء بنك (Attijariwafa Bank):</b>
- <b>صاحب الحساب:</b> اسم صاحب حساب التجاري
- <b>رقم الحساب (RIB):</b> <code>ريب التجاري</code>

<b>سياش بنك (CIH Bank):</b>
- <b>صاحب الحساب:</b> اسم صاحب حساب سياش
- <b>رقم الحساب (RIB):</b> <code>ريب سياش</code>

بعد إتمام الدفع، يرجى إرسال لقطة شاشة للإيصال <b>مع ID الخاص بك على تليجرام</b> إلى الأدمن للتحقق وتفعيل حسابك:
👨‍💻 <b>تواصل مع الأدمن:</b> """ + ADMIN_CONTACT_INFO + """
""",
        "payment_invoice_title": "سيرفر SSH مدفوع",
        "payment_invoice_description": "اشتراك لمدة 30 يومًا في سيرفر SSH عالي السرعة.",
        "payment_not_configured": "عذراً، طريقة الدفع هذه غير مهيأة بعد. يرجى التواصل مع الأدمن.",
        "payment_successful_creation": "✅ تم الدفع بنجاح! تفاصيل حسابك:",
    },
    'en': {
        # ... (يمكنك إضافة النصوص الإنجليزية هنا بنفس الطريقة) ...
    }
}
