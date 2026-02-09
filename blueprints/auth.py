from flask import Blueprint, render_template, request, redirect, url_for, session
from database.models import db, Admin

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    # اگر ادمین وجود دارد، نیازی به نصب نیست
    if Admin.query.first():
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # ساخت ادمین جدید
        new_admin = Admin(username=username)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()
        
        return redirect(url_for('auth.login'))
        
    return render_template('setup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = Admin.query.filter_by(username=username).first()
        
        # بررسی صحت پسورد
        if user and user.check_password(password):
            session['admin_id'] = user.id
            # --- اصلاح مهم: تغییر مسیر به index ---
            return redirect(url_for('index'))
            
        return render_template('login.html', error="Invalid Credentials")
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('auth.login'))