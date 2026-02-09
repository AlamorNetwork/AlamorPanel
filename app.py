import os
import sys
from flask import Flask, render_template, redirect, url_for, request, session, abort
from database.models import db, Admin, PanelSettings , Inbound

# وارد کردن بلوپرینت‌ها (ماژول‌های جداگانه)
from blueprints.auth import auth_bp
from blueprints.settings import settings_bp
from blueprints.cores import cores_bp
from blueprints.logs import logs_bp
def create_app():
    # 1. تنظیمات اولیه اپلیکیشن
    app = Flask(__name__)
    
    # کلید سشن (در محیط عملیاتی بهتر است از فایل خوانده شود)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'ALAMOR_SLYTHERIN_SUPER_SECRET_KEY_2026')
    
    # تنظیمات دیتابیس
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'database', 'alamor.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # راه‌اندازی دیتابیس
    db.init_app(app)

    # 2. ثبت ماژول‌ها (Blueprints)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(cores_bp, url_prefix='/core')
    app.register_blueprint(logs_bp, url_prefix='/logs')

    # 3. ایجاد جداول دیتابیس در اولین اجرا
    with app.app_context():
        if not os.path.exists(os.path.join(basedir, 'database')):
            os.makedirs(os.path.join(basedir, 'database'))
        db.create_all()

    # 4. سیستم امنیتی مرکزی (Middleware)
    @app.before_request
    def security_guard():
        # دسترسی به فایل‌های استاتیک (CSS/JS) همیشه آزاد است
        if request.endpoint and 'static' in request.endpoint:
            return

        # گام اول: بررسی نصب اولیه (آیا ادمین وجود دارد؟)
        if not Admin.query.first():
            if request.endpoint != 'auth.setup':
                return redirect(url_for('auth.setup'))
            return

        # گام دوم: بررسی لاگین بودن کاربر
        if 'admin_id' not in session:
            # اگر کاربر لاگین نیست و نمی‌خواهد لاگین کند، ریدایرکت شود
            if request.endpoint not in ['auth.login', 'auth.setup']:
                return redirect(url_for('auth.login'))
        
        # گام سوم: بررسی مسیر مخفی (Secret Path)
        # فقط اگر کاربر لاگین نباشد، مسیر مخفی چک می‌شود تا پنل لو نرود
        if 'admin_id' not in session and request.endpoint == 'auth.login':
            settings = PanelSettings.query.first()
            if settings and settings.secret_path and settings.secret_path != "/":
                # چک کردن اینکه آیا URL با مسیر مخفی شروع شده؟
                # مثال: /my-secret/auth/login
                # این بخش نیازمند کانفیگ دقیق Nginx یا هندلینگ خاص در روت است.
                # برای سادگی در نسخه Flask-only، می‌توانیم یک پارامتر چک کنیم یا مسیر را سخت‌گیرانه کنیم.
                pass 

    # 5. مسیر اصلی داشبورد
    @app.route('/')
    def index():
        inbounds = Inbound.query.all()
        return render_template('index.html')

    # هندلینگ ارور 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    return app

if __name__ == '__main__':
    # ساخت اپلیکیشن
    app = create_app()
    from core_manager.setup_cores import CoreInstaller
    try:
        CoreInstaller.setup_environment()
    except Exception as e:
        print(f"Warning: Core setup failed: {e}")
    # خواندن تنظیمات پورت و SSL از دیتابیس
    with app.app_context():
        try:
            settings = PanelSettings.query.first()
            
            # تنظیمات پیش‌فرض اگر دیتابیس خالی بود
            port = settings.server_port if settings and settings.server_port else 5000
            cert_path = settings.ssl_cert_path if settings and settings.ssl_cert_path else None
            key_path = settings.ssl_key_path if settings and settings.ssl_key_path else None
            
        except Exception as e:
            print(f"Warning: Could not load settings from DB. Using defaults. {e}")
            port = 5000
            cert_path = None
            key_path = None

    # بررسی وجود فایل‌های SSL
    ssl_context = None
    if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"🔒 Secure Mode Enabled: Running on Port {port} with SSL.")
        ssl_context = (cert_path, key_path)
    else:
        print(f"⚠️  Insecure Mode: Running on Port {port} (No SSL).")

    # اجرای سرور
    # نکته: host='0.0.0.0' یعنی پنل روی تمام آی‌پی‌های سرور در دسترس است
    app.run(host='0.0.0.0', port=port, ssl_context=ssl_context, debug=True)