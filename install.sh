#!/bin/bash
# Final Version: A robust, self-contained installer for the modular bot project.
# This script is specifically designed for the separated file structure.

# ========================================================================
#      السكربت الصحيح والمتوافق لتثبيت المشروع المقسم
# ========================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# --- إعدادات أساسية ---
GIT_REPO_URL="https://github.com/Lahcenoum/sshby.git"
PROJECT_DIR="/home/ssh_bot"
SSH_CONNECTION_LIMIT=2

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
echo "      🔧 بدء التثبيت الكامل للبوت (بنية مقسمة)"
echo "=================================================="

# الخطوة 0: حذف أي تثبيت قديم
echo -e "\n[0/9] 🗑️ حذف أي تثبيت قديم..."
systemctl stop ssh_bot.service >/dev/null 2>&1 || true
systemctl disable ssh_bot.service >/dev/null 2>&1 || true
rm -f /etc/systemd/system/ssh_bot.service
rm -rf "$PROJECT_DIR"
green "  - ✅ تم تنظيف أي تثبيتات سابقة."

# 1. تحديث النظام وتثبيت المتطلبات
echo -e "\n[1/9] 📦 تحديث النظام وتثبيت المتطلبات الأساسية..."
apt-get update >/dev/null 2>&1
apt-get install -y git python3-venv python3-pip openssl sudo curl cron >/dev/null 2>&1
green "  - ✅ تم تثبيت المتطلبات."

# 2. التأكد من أن خدمة cron تعمل
echo -e "\n[2/9] ⏰ التأكد من تشغيل خدمة cron..."
systemctl start cron
systemctl enable cron
green "  - ✅ خدمة cron تعمل الآن."

# 3. استنساخ المشروع
echo -e "\n[3/9] 📥 استنساخ المشروع من GitHub..."
git clone "$GIT_REPO_URL" "$PROJECT_DIR"
cd "$PROJECT_DIR" || { red "❌ فشل الدخول إلى مجلد المشروع."; exit 1; }
green "  - ✅ تم تحميل المشروع بنجاح."

# 4. إعداد ملف التكوين (bot_config.py)
echo -e "\n[4/9] 🔑 إعداد ملف التكوين..."
CONFIG_FILE="$PROJECT_DIR/bot_config.py"
if [ ! -f "$CONFIG_FILE" ]; then
    red "❌ ملف الإعدادات 'bot_config.py' غير موجود في المستودع!"; exit 1;
fi

# طلب التوكن والتحقق منه
read -p "  - أدخل توكن البوت من BotFather: " BOT_TOKEN
while [ -z "$BOT_TOKEN" ]; do
    yellow "  - التوكن لا يمكن أن يكون فارغاً. يرجى المحاولة مرة أخرى."
    read -p "  - أدخل توكن البوت من BotFather: " BOT_TOKEN
done

# طلب معرف الأدمن والتحقق منه
read -p "  - أدخل معرف الأدمن الرقمي الخاص بك (Admin ID): " ADMIN_ID
while ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; do
    yellow "  - المعرف يجب أن يكون رقمياً فقط. يرجى المحاولة مرة أخرى."
    read -p "  - أدخل معرف الأدمن الرقمي الخاص بك (Admin ID): " ADMIN_ID
done

sed -i "s/^TOKEN = \"YOUR_TELEGRAM_BOT_TOKEN\".*/TOKEN = \"$BOT_TOKEN\"/" "$CONFIG_FILE"
sed -i "s/^ADMIN_USER_ID = .*/ADMIN_USER_ID = $ADMIN_ID/" "$CONFIG_FILE"
green "  - ✅ تم تحديث التوكن ومعرف الأدمن في 'bot_config.py'."

# 5. إعداد سكربتات SSH
echo -e "\n[5/9] 👤 إعداد سكربتات SSH..."
if [ -f "create_ssh_user.sh" ]; then
    mv "create_ssh_user.sh" "/usr/local/bin/"
    chmod +x "/usr/local/bin/create_ssh_user.sh"
    green "  - ✅ تم إعداد سكربت إنشاء المستخدمين."
else
    yellow "  - ⚠️ تحذير: لم يتم العثور على 'create_ssh_user.sh'."
fi
# ... (يمكن إضافة باقي سكربتات SSH هنا بنفس الطريقة) ...

# 6. إعداد النسخ الاحتياطي التلقائي
echo -e "\n[6/9] 🗄️ إعداد النسخ الاحتياطي التلقائي..."
read -p "  - أدخل معرف القناة (Channel ID) لإرسال النسخ الاحتياطية (يبدأ بـ -100): " CHANNEL_ID
while [[ ! "$CHANNEL_ID" =~ ^-100[0-9]+$ ]]; do
    yellow "  - المعرف غير صالح. يجب أن يكون رقمًا ويبدأ بـ -100."
    read -p "  - أدخل معرف القناة (Channel ID): " CHANNEL_ID
done

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
{ crontab -l 2>/dev/null | grep -v -F "/usr/local/bin/backup_bot.sh"; echo "0 */6 * * * /usr/local/bin/backup_bot.sh"; } | crontab -
green "  - ✅ تم إعداد مهمة النسخ الاحتياطي كل 6 ساعات."

# 7. إعداد بيئة بايثون
echo -e "\n[7/9] 🐍 إعداد البيئة الافتراضية وتثبيت المكتبات..."
python3 -m venv venv
(
    source venv/bin/activate
    pip install --upgrade pip >/dev/null 2>&1
    if [ ! -f "requirements.txt" ]; then
        red "❌ ملف 'requirements.txt' غير موجود!"
        exit 1
    fi
    pip install -r requirements.txt >/dev/null 2>&1
    green "  - ✅ تم تثبيت جميع المكتبات من 'requirements.txt'."
)

# 8. إعداد وتشغيل الخدمة
echo -e "\n[8/9] 🚀 إعداد وتشغيل خدمة البوت..."
cat > /etc/systemd/system/ssh_bot.service << EOL
[Unit]
Description=Telegram SSH Bot Service (Modular)
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python3 ${PROJECT_DIR}/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL
green "  - ✅ تم إنشاء ملف الخدمة بنجاح."

# 9. تشغيل الخدمة
echo -e "\n[9/9] ⚡️ تفعيل وتشغيل الخدمة النهائية..."
systemctl daemon-reload
systemctl enable ssh_bot.service >/dev/null 2>&1
systemctl restart ssh_bot.service

# --- نهاية التثبيت ---
echo "=================================================="
green "🎉 اكتمل التثبيت بنجاح!"
echo "--------------------------------------------------"
echo "  - 🤖 لمراقبة حالة البوت، استخدم الأمر:"
echo "    ${yellow}systemctl status ssh_bot.service"
echo ""
echo "  - 📜 لعرض سجلات (logs) البوت، استخدم الأمر:"
echo "    ${yellow}journalctl -u ssh_bot.service -f --no-pager"
echo ""
echo "  - 🗄️ تم إعداد النسخ الاحتياطي لقاعدة البيانات كل 6 ساعات."
echo "=================================================="
