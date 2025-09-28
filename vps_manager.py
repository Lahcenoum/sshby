import subprocess
import random
import string
import sqlite3
from datetime import datetime

# --- الإعدادات الأساسية لإدارة السيرفر ---
SSH_SCRIPT_PATH = '/usr/local/bin/create_ssh_user.sh'
DB_FILE = 'ssh_bot_users.db'

def create_ssh_user(telegram_user_id: int, username: str, expiry_days: int):
    """
    ينشئ مستخدم SSH على السيرفر ويسجله في قاعدة البيانات.
    """
    try:
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        command_to_run = ["sudo", SSH_SCRIPT_PATH, username, password, str(expiry_days)]

        # تنفيذ الأمر لإنشاء المستخدم على السيرفر
        process = subprocess.run(command_to_run, capture_output=True, text=True, timeout=30, check=True)
        
        # تسجيل المستخدم في قاعدة البيانات
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO ssh_accounts (telegram_user_id, ssh_username, ssh_password, created_at) VALUES (?, ?, ?, ?)",
                         (telegram_user_id, username, password, datetime.now()))
            conn.commit()
        
        print(f"Successfully created SSH user '{username}' for telegram_user_id '{telegram_user_id}'.")
        return username, password

    except subprocess.CalledProcessError as e:
        print(f"Error executing SSH script for user '{username}'. Return code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred in create_ssh_user for '{username}': {e}")
        return None, None


def get_user_expiry(username: str) -> str:
    """
    يتحقق من تاريخ انتهاء صلاحية حساب مستخدم معين على السيرفر.
    """
    try:
        expiry_output = subprocess.check_output(['/usr/bin/chage', '-l', username], text=True, stderr=subprocess.DEVNULL)
        expiry_line = next((line for line in expiry_output.split('\n') if "Account expires" in line), None)
        expiry_date = expiry_line.split(':', 1)[1].strip() if expiry_line else "N/A"
        return expiry_date
    except Exception:
        return "N/A"
