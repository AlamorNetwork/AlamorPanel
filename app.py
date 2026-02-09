from flask import Flask, render_template
from database.models import db
import os

def create_app():
    app = Flask(__name__)
    
    # تنظیمات دیتابیس
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'alamor.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # ساخت دیتابیس در اولین اجرا
    with app.app_context():
        if not os.path.exists('database'):
            os.makedirs('database')
        db.create_all()

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

# در انتهای فایل app.py
if __name__ == '__main__':
    app = create_app()
    # اجرای مستقیم روی پورت 5000 با قابلیت Auto-Reload
    app.run(host='0.0.0.0', port=5000, debug=True)