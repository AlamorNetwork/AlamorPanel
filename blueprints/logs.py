from flask import Blueprint, render_template
import subprocess

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/')
def view_logs():
    # خواندن لاگ‌های Xray (فرض بر این است که در مسیر استاندارد هستند)
    # یا خواندن ژورنال سیستم
    logs = []
    try:
        # خواندن 50 خط آخر سرویس Xray
        result = subprocess.check_output(["journalctl", "-u", "xray", "-n", "50", "--no-pager"], text=True)
        logs = result.splitlines()
    except Exception as e:
        logs = [f"Error reading logs: {str(e)}", "Make sure Xray service is running."]

    return render_template('logs.html', logs=logs)