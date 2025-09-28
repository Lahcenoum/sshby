#!/bin/bash
# Final Version: Adapted for the modular project structure (bot, payments, vps_manager, etc.)

# ========================================================================
#      سكريبت التثبيت المتوافق مع المشروع المقسم
# ========================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# --- إعدادات أساسية (يمكن تعديلها) ---
# ❗️ غير رابط المستودع إلى رابط المستودع الخاص بك على GitHub
GIT_REPO_URL="https://github.com/YourUsername/YourBotRepo.git"
PROJECT_DIR="/home/ssh_bot"
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

clear
echo "=================================================="
echo "      🔧 بدء التثبيت الكامل للبوت المقسم"
echo "=================================================="

# --- القسم الأول: تثبيت بوت التليجرام ---

# الخطوة 0: حذف أي تثبيت قديم
echo -e "\n[0/10] 🗑️ حذف أي تثبيت قديم..."
systemctl stop ssh_bot.service >/dev/null 2>&1 || true
systemctl disable ssh_bot.service >/dev/null 2>&1 || true
rm -f /etc/systemd/system/ssh_bot.service
rm -rf "$PROJECT_DIR"

# 1. تحديث النظام وتثبيت المتطلبات
echo -e "\n[1/10] 📦 تحديث النظام وتثبيت المتطلبات الأساسية..."
apt-get update
apt-get install -y git python3-venv python3-pip openssl sudo curl cron

# 2. التأكد من أن خدمة cron تعمل
echo -e "\n[2/10] ⏰ التأكد من تشغيل خدمة cron..."
systemctl start cron
systemctl enable cron
green "  - ✅ خدمة cron تعمل الآن."

# 3. استنساخ المشروع
echo -e "\n[3/10] 📥 استنساخ المشروع من GitHub..."
git clone "$GIT_REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# 4. إعداد ملف التكوين (bot_config.py)
echo -e "\n[4/10] 🔑 إعداد ملف التكوين..."
CONFIG_FILE="$PROJECT_DIR/bot_config.py"
if [ ! -f "$CONFIG_FILE" ]; then
    red "❌ ملف الإعدادات 'bot_config.py' غير موجود في المستودع!"; exit 1;
fi

read -p "  - أدخل توكن البوت من BotFather: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then red "❌ لم يتم إدخال التوكن."; exit 1; fi

read -p "  - أدخل معرف الأدمن الرقمي الخاص بك (Admin ID): " ADMIN_ID
if ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
    red "❌ المعرف يجب أن يكون رقمياً فقط."
    exit 1
fi

sed -i "s/^TOKEN = \"YOUR_TELEGRAM_BOT_TOKEN\".*/TOKEN = \"$BOT_TOKEN\"/" "$CONFIG_FILE"
sed -i "s/^ADMIN_USER_ID = .*/ADMIN_USER_ID = $ADMIN_ID/" "$CONFIG_FILE"
green "  - ✅ تم تحديث التوكن ومعرف الأدمن بنجاح."

# 5. إعداد سكربتات SSH
echo -e "\n[5/10] 👤 إعداد سكربتات SSH..."
read -p "  - أدخل عنوان IP الخاص بسيرفرك: " SERVER_IP
if [ -z "$SERVER_IP" ]; then red "❌ لم يتم إدخال الآي بي."; exit 1; fi

# نفترض أن السكربتات موجودة في المستودع
if [ -f "create_ssh_user.sh" ]; then
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

# 6. إعداد النسخ الاحتياطي التلقائي
echo -e "\n[6/10] 🗄️ إعداد النسخ الاحتياطي التلقائي لقاعدة البيانات..."
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
CAPTION="نسخة احتياطية جديدة لقاعدة بيانات البوت - \$(date)"

if [ ! -f "\$DB_PATH" ]; then exit 1; fi
BACKUP_FILE="/tmp/db_backup_\$(date +%F_%H-%M-%S).db"
cp "\$DB_PATH" "\$BACKUP_FILE"
curl -s -F "chat_id=\${CHANNEL_ID}" -F "document=@\${BACKUP_FILE}" -F "caption=\${CAPTION}" "https://api.telegram.org/bot\${BOT_TOKEN}/sendDocument" > /dev/null
rm "\$BACKUP_FILE"
EOL

chmod +x /usr/local/bin/backup_bot.sh
{ crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/backup_bot.sh"; echo "0 */10 * * * /usr/local/bin/backup_bot.sh"; } | crontab -
green "  - ✅ تم إعداد مهمة النسخ الاحتياطي كل 10 ساعات بنجاح."

# 7. إعداد بيئة بايثون
echo -e "\n[7/10] 🐍 إعداد البيئة الافتراضية وتثبيت المكتبات..."
python3 -m venv venv
(
    source venv/bin/activate
    pip install --upgrade pip
    if [ ! -f "requirements.txt" ]; then
        red "❌ ملف 'requirements.txt' غير موجود. لا يمكن تثبيت المكتبات."
        exit 1
    fi
    pip install -r requirements.txt
    green "  - ✅ تم تثبيت جميع المكتبات من requirements.txt بنجاح."
)

# 8. إعداد وتشغيل الخدمة
echo -e "\n[8/10] 🚀 إعداد وتشغيل خدمة البوت..."
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python3 ${PROJECT_DIR}/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL
green "  - ✅ تم إنشاء ملف الخدمة بنجاح."

# 9. تشغيل الخدمة
echo -e "\n[9/10] ⚡️ تفعيل وتشغيل الخدمة النهائية..."
systemctl daemon-reload
systemctl enable ssh_bot.service >/dev/null 2>&1
systemctl restart ssh_bot.service

# 10. نهاية التثبيت
echo -e "\n[10/10] 🎉 تم التثبيت بنجاح!"
echo "=================================================="
green "🎉 اكتمل التثبيت بنجاح!"
echo "--------------------------------------------------"
echo "  - 🤖 لمراقبة حالة البوت، استخدم الأمر:"
echo "    ${yellow}systemctl status ssh_bot.service"
echo ""
echo "  - 📜 لعرض سجلات (logs) البوت، استخدم الأمر:"
echo "    ${yellow}journalctl -u ssh_bot.service -f --no-pager"
echo ""
echo "  - 🗄️ تم إعداد النسخ الاحتياطي لقاعدة البيانات كل 10 ساعات."
echo "=================================================="
