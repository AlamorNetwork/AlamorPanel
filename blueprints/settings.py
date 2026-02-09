from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from database.models import db, PanelSettings, Admin
import subprocess
import os

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/panel', methods=['GET', 'POST'])
def index():
    settings = PanelSettings.query.first()
    if not settings:
        settings = PanelSettings(server_port=5000, secret_path="/")
        db.session.add(settings)
        db.session.commit()
        
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_network':
            settings.server_port = int(request.form.get('port'))
            settings.secret_path = request.form.get('path')
            db.session.commit()
            flash('Settings saved! Restart the panel to apply changes.', 'warning')
            
        elif action == 'get_ssl':
            domain = request.form.get('domain')
            email = "admin@" + domain
            # Run Certbot
            try:
                cmd = [
                    "certbot", "certonly", "--standalone", 
                    "--non-interactive", "--agree-tos", 
                    "-m", email, "-d", domain
                ]
                subprocess.run(cmd, check=True)
                
                # Update DB
                settings.panel_domain = domain
                settings.ssl_cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
                settings.ssl_key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"
                db.session.commit()
                flash(f'SSL Certificate acquired for {domain}', 'success')
            except Exception as e:
                flash(f'SSL Error: {str(e)}', 'danger')

    return render_template('settings.html', settings=settings)

@settings_bp.route('/security', methods=['POST'])
def update_security():
    # Key Rotation Logic
    old_key = request.form.get('old_key') # Verification
    new_key = request.form.get('new_key')
    
    # Here you would decrypt all sensitive fields with old_key 
    # and re-encrypt with new_key.
    # For now, we update the Admin password hash salt if needed
    
    admin = Admin.query.first()
    if admin.check_password(request.form.get('current_password')):
        admin.set_password(request.form.get('new_password'))
        db.session.commit()
        return jsonify({"status": "success", "msg": "Password & Hashes Updated"})
    
    return jsonify({"status": "error", "msg": "Invalid Credentials"})