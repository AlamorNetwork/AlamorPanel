from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    id = db.Column(db.Integer, primary_key=True)
    enable = db.Column(db.Boolean, default=True)
    remark = db.Column(db.String(100))
    protocol = db.Column(db.String(20)) # vless, vmess, etc.
    port = db.Column(db.Integer, unique=True)
    listen = db.Column(db.String(50), default="0.0.0.0")
    
    total = db.Column(db.BigInteger, default=0) # Total Flow
    expiry_time = db.Column(db.BigInteger, default=0) # Duration
    
    # تمام تنظیمات خاص پروتکل (Reality, TLS, Authentication)
    settings = db.Column(db.Text) 
    
    # تمام تنظیمات انتقال (Transmission, TCP, Reality advanced)
    stream_settings = db.Column(db.Text)
    
    # تنظیمات سیستمی (Sniffing, Sockopt, TProxy)
    sniffing = db.Column(db.Text)
    sockopt = db.Column(db.Text)