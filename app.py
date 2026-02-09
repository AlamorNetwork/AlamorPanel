import os
import sys
from flask import Flask, render_template, redirect, url_for, request, session, abort
# ایمپورت مدل Inbound ضروری است
from database.models import db, Admin, PanelSettings, Inbound

# وارد کردن بلوپرینت‌ها
from blueprints.auth import auth_bp
from blueprints.settings import settings_bp
from blueprints.cores import cores_bp
from blueprints.logs import logs_bp

def create_app():
    # 1. تنظیمات اولیه
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'ALAMOR_SLYTHERIN_SUPER_SECRET_2026')
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'database', 'alamor.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # 2. ثبت ماژول‌ها
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(cores_bp, url_prefix='/core')
    app.register_blueprint(logs_bp, url_prefix='/logs')

    # 3. ایجاد دیتابیس در صورت نبودن
    with app.app_context():
        if not os.path.exists(os.path.join(basedir, 'database')):
            os.makedirs(os.path.join(basedir, 'database'))
        db.create_all()

    # 4. گارد امنیتی
    @app.before_request
    def security_guard():
        if request.endpoint and 'static' in request.endpoint:
            return

        # بررسی نصب بودن
        if not Admin.query.first():
            if request.endpoint != 'auth.setup':
                return redirect(url_for('auth.setup'))
            return

        # بررسی لاگین بودن
        if 'admin_id' not in session:
            if request.endpoint not in ['auth.login', 'auth.setup']:
                return redirect(url_for('auth.login'))

    # 5. صفحه اصلی (داشبورد) - اصلاح شده
    @app.route('/')
    def index():
        # --- تغییر مهم: خواندن لیست کانفیگ‌ها از دیتابیس ---
        try:
            # دریافت همه اینباندها (جدیدترین‌ها اول)
            inbounds = Inbound.query.order_by(Inbound.id.desc()).all()
        except:
            inbounds = []
            
        # ارسال لیست به قالب HTML
        return render_template('index.html', inbounds=inbounds)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    return app

if __name__ == '__main__':
    app = create_app()
    
    # نصب خودکار هسته Xray هنگام اجرا
    from core_manager.setup_cores import CoreInstaller
    try:
        CoreInstaller.setup_environment()
    except Exception as e:
        print(f"Core Setup Warning: {e}")

    # لود تنظیمات SSL و پورت
    with app.app_context():
        try:
            settings = PanelSettings.query.first()
            port = settings.server_port if settings and settings.server_port else 5000
            cert = settings.ssl_cert_path if settings and settings.ssl_cert_path else None
            key = settings.ssl_key_path if settings and settings.ssl_key_path else None
        except:
            port = 5000
            cert = None
            key = None

    ssl_context = (cert, key) if cert and key and os.path.exists(cert) else None
    
    print(f"🚀 AlamorPanel Running on Port {port}")
    app.run(host='0.0.0.0', port=port, ssl_context=ssl_context, debug=True)