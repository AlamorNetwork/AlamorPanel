from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class AdminUser(db.Model):
    """تیبل مدیران پنل برای لاگین"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # هش شده

class Inbound(db.Model):
    """تیبل اصلی کانفیگ‌ها (Sing-box/Hysteria)"""
    id = db.Column(db.Integer, primary_key=True)
    remark = db.Column(db.String(100)) # نام دلخواه
    protocol = db.Column(db.String(20)) # vless, hysteria2, etc.
    port = db.Column(db.Integer, unique=True, nullable=False)
    uuid_auth = db.Column(db.String(100), nullable=False) # UUID یا پسورد
    settings = db.Column(db.Text) # تنظیمات اضافی به صورت JSON String
    enable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SSLCert(db.Model):
    """تیبل مدیریت گواهینامه‌ها"""
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(100), unique=True)
    cert_path = db.Column(db.String(255))
    key_path = db.Column(db.String(255))
    expiry_date = db.Column(db.DateTime)

class SystemSetting(db.Model):
    """تنظیمات عمومی پنل"""
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text)

class TrafficLog(db.Model):
    """ثبت مصرف ترافیک"""
    id = db.Column(db.Integer, primary_key=True)
    inbound_id = db.Column(db.Integer, db.ForeignKey('inbound.id'))
    upload = db.Column(db.BigInteger, default=0)
    download = db.Column(db.BigInteger, default=0)
    last_update = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Inbound(db.Model):
    """
    هسته اصلی: مدل اینباند که تمام پروتکل‌های Xray را پشتیبانی می‌کند
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # --- فیلدهای مدیریتی پنل (قابل جستجو) ---
    enable = db.Column(db.Boolean, default=True)
    remark = db.Column(db.String(100))           # نام کانفیگ
    port = db.Column(db.Integer, unique=True, nullable=False)
    protocol = db.Column(db.String(50), nullable=False) # vless, vmess, trojan, wireguard, etc.
    listen = db.Column(db.String(50), default="0.0.0.0")
    
    # --- آمار و محدودیت‌ها ---
    total = db.Column(db.BigInteger, default=0)  # حجم کل مجاز (0 = نامحدود)
    up = db.Column(db.BigInteger, default=0)     # آپلود مصرفی
    down = db.Column(db.BigInteger, default=0)   # دانلود مصرفی
    expiry_time = db.Column(db.BigInteger, default=0) # زمان انقضا (Timestamp)
    
    # --- شناسه داخلی Xray ---
    # تگ برای روتینگ و آمارگیری در هسته Xray استفاده می‌شود
    tag = db.Column(db.String(100), unique=True) 

    # --- فیلدهای پیکربندی Xray (JSON TEXT) ---
    # استفاده از Text برای ذخیره کامل ساختار جیسون طبق داکیومنت Xray
    
    # شامل: clients, users, fallbacks, decryption, etc.
    settings = db.Column(db.Text, default="{}")
    
    # شامل: network (tcp, ws, grpc, xhttp), security (tls, reality), sockopt (tproxy, mark)
    stream_settings = db.Column(db.Text, default="{}")
    
    # شامل: enabled, destOverride, routeOnly
    sniffing = db.Column(db.Text, default="{}")
    
    # شامل: strategy, refresh, concurrency (allocation)
    allocate = db.Column(db.Text, default="{}")

    def get_settings(self):
        """بازگرداندن تنظیمات به صورت دیکشنری پایتون"""
        try:
            return json.loads(self.settings) if self.settings else {}
        except:
            return {}

    def get_stream(self):
        """بازگرداندن تنظیمات استریم به صورت دیکشنری"""
        try:
            return json.loads(self.stream_settings) if self.stream_settings else {}
        except:
            return {}
    
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PanelSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server_port = db.Column(db.Integer, default=5000)
    panel_domain = db.Column(db.String(100))
    secret_path = db.Column(db.String(50), default="/")
    sub_port = db.Column(db.Integer, default=2096)
    ssl_cert_path = db.Column(db.String(200))
    ssl_key_path = db.Column(db.String(200))
    system_secret_key = db.Column(db.String(100))