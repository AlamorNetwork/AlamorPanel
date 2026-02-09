from flask import Flask, render_template
from database.models import db
import os

def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'alamor.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        if not os.path.exists('database'):
            os.makedirs('database')
        db.create_all()
    
    @app.route('/')
    def index():
        # حتماً نام فایل را با فایلی که در templates داری یکی کن
        return render_template('index.html')

    return app  # این خط حیاتی است و در کد شما جا افتاده بود

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)