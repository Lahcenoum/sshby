import subprocess
import random
import string
import sqlite3
from datetime import datetime
from bot_config import DB_FILE # استيراد مسار قاعدة البيانات

# المسار إلى سكربت bash لإنشاء المستخدمين
# تأكد من أن هذا السكربت موجود في المستودع الخاص بك على GitHub
SSH_SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'

def create_ssh_user(telegram_user_id: int, username: str, expiry_days: int) -> tuple[str | None, str | None]:
    """
    ينشئ حساب SSH جديد باستخدام سكربت bash.
    يسجل الحساب في قاعدة البيانات عند النجاح.
    Returns: A tuple of (username, password) on success, or (None, None) on failure.
    """
    try:
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        command = ["sudo", SSH_SCRIPT_PATH, username, password, str(expiry_days)]
        
        # تنفيذ الأمر
        process = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
        
        # إذا نجح الأمر، قم بتسجيل الحساب في قاعدة البيانات
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT INTO ssh_accounts (telegram_user_id, ssh_username, ssh_password, created_at) VALUES (?, ?, ?, ?)",
                (telegram_user_id, username, password, datetime.now())
            )
            conn.commit()
        
        print(f"Successfully created SSH user: {username}")
        return username, password

    except FileNotFoundError:
        print(f"ERROR: SSH script not found at {SSH_SCRIPT_PATH}")
        return None, None
    except subprocess.CalledProcessError as e:
        print(f"ERROR: SSH script failed for user {username}. Exit code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred in create_ssh_user: {e}")
        return None, None

def get_user_expiry(username: str) -> str:
    """
    يتحقق من تاريخ انتهاء صلاحية حساب المستخدم على السيرفر.
    Returns: The expiry date as a string, or "N/A" if not found or on error.
    """
    try:
        # استخدام أمر chage للتحقق من تاريخ انتهاء الصلاحية
        expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, stderr=subprocess.DEVNULL)
        # البحث عن السطر الذي يحتوي على تاريخ انتهاء الصلاحية
        for line in expiry_output.split('\n'):
            if "Account expires" in line:
                expiry_date = line.split(':', 1)[1].strip()
                return expiry_date if expiry_date != "never" else "لا ينتهي"
        return "غير محدد"
    except (subprocess.CalledProcessError, FileNotFoundError):
        # في حالة وجود خطأ (مثل عدم العثور على المستخدم)، يتم إرجاع "N/A"
        return "N/A"
    except Exception as e:
        print(f"An unexpected error occurred in get_user_expiry for {username}: {e}")
        return "N/A"
