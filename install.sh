#!/bin/bash
# Final Version: Focuses on SSH-only setup, PayPal, and Moroccan banks integration.

# ========================================================================
#        سكريبت التثبيت (SSH + PayPal + Moroccan Banks)
# ========================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# --- إعدادات أساسية ---
GIT_REPO_URL="https://github.com/Lahcenoum/sshtestbot.git" # استبدل هذا برابط المستودع الخاص بك إذا اختلف
PROJECT_DIR="/home/ssh_paypal_bot" # تم تغيير المسار لتجنب التعارض
BOT_FILE_NAME="bot.py" # اسم ملف البوت الرئيسي
SSH_CONNECTION_LIMIT=2 # حد الاتصالات لخدمة SSH

# --- نهاية قسم الإعدادات ---

# --- دوال الألوان ---
red() { echo -e "\e[31m$*\e[0m"; }
green() { echo -e "\e[32m$*\e[0m"; }
yellow() { echo -e "\e[33m$*\e[0m"; }

# التحقق من صلاحيات الجذر
if [ "$(id -u)" -ne 0 ]; then
    red "❌ يجب تشغيل السكربت بصلاحيات root."
    exit 1
fi

echo "=================================================="
echo "      🔧 بدء التثبيت الكامل للبوت (مع PayPal)"
echo "=================================================="

# --- القسم الأول: تثبيت بوت التليجرام ---

# الخطوة 0: حذف أي تثبيت قديم
echo -e "\n[0/12] 🗑️ حذف أي تثبيت قديم..."
systemctl stop ssh_bot.service >/dev/null 2>&1 || true
systemctl disable ssh_bot.service >/dev/null 2>&1 || true
rm -f /etc/systemd/system/ssh_bot.service
rm -rf "$PROJECT_DIR"

# 1. تحديث النظام وتثبيت المتطلبات
echo -e "\n[1/12] 📦 تحديث النظام وتثبيت المتطلبات الأساسية..."
apt-get update
apt-get install -y git python3-venv python3-pip openssl sudo curl cron

# 2. التأكد من أن خدمة cron تعمل
echo -e "\n[2/12] ⏰ التأكد من تشغيل خدمة cron..."
systemctl start cron
systemctl enable cron
green "  - ✅ خدمة cron تعمل الآن."

# 3. استنساخ المشروع
echo -e "\n[3/12] 📥 استنساخ المشروع من GitHub..."
git clone "$GIT_REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# 4. إدخال معلومات البوت الأساسية
echo -e "\n[4/12] 🔑 إعداد معلومات البوت الأساسية..."
read -p "  - أدخل توكن البوت: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then red "❌ لم يتم إدخال التوكن."; exit 1; fi
sed -i "s|^TOKEN = \".*\"|TOKEN = \"$BOT_TOKEN\"|" "$PROJECT_DIR/$BOT_FILE_NAME"

read -p "  - أدخل ID الأدمن الرقمي: " ADMIN_ID
if ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then red "❌ الـ ID يجب أن يكون رقمًا."; exit 1; fi
sed -i "s|^ADMIN_USER_ID = .*|ADMIN_USER_ID = $ADMIN_ID|" "$PROJECT_DIR/$BOT_FILE_NAME"

read -p "  - أدخل اسم مستخدم الأدمن (مع @): " ADMIN_USERNAME
if [ -z "$ADMIN_USERNAME" ]; then red "❌ لم يتم إدخال اسم المستخدم."; exit 1; fi
sed -i "s|^ADMIN_CONTACT_INFO = \".*\"|ADMIN_CONTACT_INFO = \"$ADMIN_USERNAME\"|" "$PROJECT_DIR/$BOT_FILE_NAME"
green "  - ✅ تم تحديث معلومات البوت الأساسية."

# 5. إعداد معلومات PayPal
echo -e "\n[5/12] 💳 إعداد معلومات الدفع عبر PayPal..."
read -p "  - أدخل PayPal Client ID: " PAYPAL_ID
if [ -z "$PAYPAL_ID" ]; then red "❌ لم يتم إدخال Client ID."; exit 1; fi
sed -i "s|YOUR_PAYPAL_CLIENT_ID|$PAYPAL_ID|" "$PROJECT_DIR/$BOT_FILE_NAME"

read -p "  - أدخل PayPal Client Secret: " PAYPAL_SECRET
if [ -z "$PAYPAL_SECRET" ]; then red "❌ لم يتم إدخال Client Secret."; exit 1; fi
sed -i "s|YOUR_PAYPAL_CLIENT_SECRET|$PAYPAL_SECRET|" "$PROJECT_DIR/$BOT_FILE_NAME"
green "  - ✅ تم تحديث معلومات PayPal."

# 6. إعداد معلومات الدفع المغربية
echo -e "\n[6/12] 🏦 إعداد معلومات الدفع المغربية..."
# التجاري وفاء بنك
read -p "  - أدخل اسم صاحب حساب التجاري وفاء بنك: " ATTIJARI_NAME
sed -i "s|اسم صاحب حساب التجاري|$ATTIJARI_NAME|" "$PROJECT_DIR/$BOT_FILE_NAME"
sed -i "s|Attijari Account Holder Name|$ATTIJARI_NAME|" "$PROJECT_DIR/$BOT_FILE_NAME"
read -p "  - أدخل رقم حساب (RIB) التجاري وفاء بنك: " ATTIJARI_RIB
sed -i "s|<code>ريب التجاري</code>|<code>$ATTIJARI_RIB</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"
sed -i "s|<code>Attijari RIB</code>|<code>$ATTIJARI_RIB</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"

# سياش بنك
read -p "  - أدخل اسم صاحب حساب سياش بنك: " CIH_NAME
sed -i "s|اسم صاحب حساب سياش|$CIH_NAME|" "$PROJECT_DIR/$BOT_FILE_NAME"
sed -i "s|CIH Account Holder Name|$CIH_NAME|" "$PROJECT_DIR/$BOT_FILE_NAME"
read -p "  - أدخل رقم حساب (RIB) سياش بنك: " CIH_RIB
sed -i "s|<code>ريب سياش</code>|<code>$CIH_RIB</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"
sed -i "s|<code>CIH RIB</code>|<code>$CIH_RIB</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"

# خدمات تحويل الأموال
read -p "  - أدخل رقم هاتف كاش بلوس: " CASHPLUS_PHONE
sed -i "s|<code>رقم هاتف كاش بلوس</code>|<code>$CASHPLUS_PHONE</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"
sed -i "s|<code>Cash Plus Phone Number</code>|<code>$CASHPLUS_PHONE</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"

read -p "  - أدخل رقم هاتف انوي موني: " INWI_PHONE
sed -i "s|<code>رقم هاتف انوي موني</code>|<code>$INWI_PHONE</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"
sed -i "s|<code>Inwi Money Phone Number</code>|<code>$INWI_PHONE</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"

read -p "  - أدخل رقم هاتف أورنج موني: " ORANGE_PHONE
sed -i "s|<code>رقم هاتف أورنج موني</code>|<code>$ORANGE_PHONE</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"
sed -i "s|<code>Orange Money Phone Number</code>|<code>$ORANGE_PHONE</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"

read -p "  - أدخل رقم هاتف MT Cash: " MTCASH_PHONE
sed -i "s|<code>رقم هاتف MT Cash</code>|<code>$MTCASH_PHONE</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"
sed -i "s|<code>MT Cash Phone Number</code>|<code>$MTCASH_PHONE</code>|" "$PROJECT_DIR/$BOT_FILE_NAME"
green "  - ✅ تم تحديث معلومات الدفع المغربية."


# 7. إعداد سكربتات SSH
echo -e "\n[7/12] 👤 إعداد سكربتات SSH..."
read -p "  - أدخل عنوان IP الخاص بسيرفرك: " SERVER_IP
if [ -z "$SERVER_IP" ]; then red "❌ لم يتم إدخال الآي بي."; exit 1; fi

if [ -f "create_ssh_user.sh" ]; then
    sed -i "s/YOUR_SERVER_IP/${SERVER_IP}/g" "create_ssh_user.sh"
    mv "create_ssh_user.sh" "/usr/local/bin/"
    chmod +x "/usr/local/bin/create_ssh_user.sh"
    green "  - ✅ تم إعداد سكربت إنشاء المستخدمين."
else
    yellow "  - ⚠️ تحذير: لم يتم العثور على 'create_ssh_user.sh'."
fi

if [ -f "delete_expired_users.sh" ]; then
    mv "delete_expired_users.sh" "/usr/local/bin/"
    chmod +x "/usr/local/bin/delete_expired_users.sh"
    { crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/delete_expired_users.sh"; echo "0 0 * * * /usr/local/bin/delete_expired_users.sh"; } | crontab -
    green "  - ✅ تم إعداد مهمة حذف الحسابات منتهية الصلاحية."
else
    yellow "  - ⚠️ تحذير: لم يتم العثور على 'delete_expired_users.sh'."
fi

if [ -f "monitor_connections.sh" ]; then
    sed -i "s/CONNECTION_LIMIT=[0-9]\+/CONNECTION_LIMIT=$SSH_CONNECTION_LIMIT/" "monitor_connections.sh"
    mv "monitor_connections.sh" "/usr/local/bin/"
    chmod +x "/usr/local/bin/monitor_connections.sh"
    { crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/monitor_connections.sh"; echo "*/1 * * * * /usr/local/bin/monitor_connections.sh"; } | crontab -
    green "  - ✅ تم إعداد مهمة مراقبة اتصالات SSH."
else
    yellow "  - ⚠️ تحذير: لم يتم العثور على 'monitor_connections.sh'."
fi

# 8. إعداد النسخ الاحتياطي التلقائي
echo -e "\n[8/12] 🗄️ إعداد النسخ الاحتياطي التلقائي لقاعدة البيانات..."
read -p "  - أدخل معرف القناة (Channel ID) لإرسال النسخ الاحتياطية إليها (يجب أن يبدأ بـ -100): " CHANNEL_ID
if [[ ! "$CHANNEL_ID" =~ ^-100[0-9]+$ ]]; then
    red "❌ المعرف غير صالح. يجب أن يكون رقمًا ويبدأ بـ -100."
    exit 1
fi

# إنشاء سكربت النسخ الاحتياطي
cat > /usr/local/bin/backup_bot.sh << EOL
#!/bin/bash
BOT_TOKEN="$BOT_TOKEN"
CHANNEL_ID="$CHANNEL_ID"
DB_PATH="$PROJECT_DIR/ssh_bot_users.db"
CAPTION="نسخة احتياطية جديدة لقاعدة بيانات المستخدمين - \$(date)"

if [ ! -f "\$DB_PATH" ]; then exit 1; fi

BACKUP_FILE="/tmp/db_backup_\$(date +%F_%H-%M-%S).db"
cp "\$DB_PATH" "\$BACKUP_FILE"

curl -s -F "chat_id=\${CHANNEL_ID}" -F "document=@\${BACKUP_FILE}" -F "caption=\${CAPTION}" "https://api.telegram.org/bot\${BOT_TOKEN}/sendDocument" > /dev/null

rm "\$BACKUP_FILE"
EOL

chmod +x /usr/local/bin/backup_bot.sh
{ crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/backup_bot.sh"; echo "0 */10 * * * /usr/local/bin/backup_bot.sh"; } | crontab -
green "  - ✅ تم إعداد مهمة النسخ الاحتياطي كل 10 ساعات بنجاح."

# 9. إعداد بيئة بايثون
echo -e "\n[9/12] 🐍 إعداد البيئة الافتراضية وتثبيت المكتبات..."
python3 -m venv venv
(
    source venv/bin/activate
    pip install --upgrade pip
    pip install python-telegram-bot paypalrestsdk
    green "  - ✅ تم تثبيت جميع المكتبات الضرورية بنجاح."
)

# 10. إعداد وتشغيل الخدمة
echo -e "\n[10/12] 🚀 إعداد وتشغيل خدمة البوت..."
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/${BOT_FILE_NAME}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL
green "  - ✅ تم إنشاء ملف الخدمة بنجاح."

# 11. إعادة تحميل وتشغيل الخدمة
echo -e "\n[11/12] 🔄 إعادة تحميل وتشغيل الخدمة النهائية..."
systemctl daemon-reload
systemctl enable ssh_bot.service >/dev/null 2>&1
systemctl restart ssh_bot.service

# 12. نهاية التثبيت
echo -e "\n[12/12] 🎉 تم التثبيت بنجاح!"
echo "=================================================="
green "🎉 تم التثبيت بنجاح!"
echo "--------------------------------------------------"
echo "  - 🤖 لمراقبة البوت: systemctl status ssh_bot.service"
echo "  - 🪵 لعرض سجلات البوت: journalctl -u ssh_bot.service -f"
echo "  - 🗄️ تم إعداد النسخ الاحتياطي لقاعدة البيانات كل 10 ساعات."
echo "=================================================="
