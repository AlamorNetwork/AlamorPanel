from flask import Blueprint, request, jsonify, render_template
from core_manager.xray_builder import XrayBuilder
from core_manager.setup_cores import CoreInstaller
from database.models import db, Inbound
import json

cores_bp = Blueprint('cores', __name__)

# --- VIEW ROUTES (صفحات HTML) ---

@cores_bp.route('/manager')
def manage():
    """صفحه مدیریت هسته و وضعیت سرویس‌ها"""
    return render_template('cores.html')


# --- API ROUTES (عملیات پشت صحنه) ---

@cores_bp.route('/restart', methods=['POST'])
def restart_core():
    """اعمال کانفیگ و ریستارت Xray"""
    success, msg = XrayBuilder.apply_config()
    if success:
        return jsonify({"status": "success", "message": msg})
    else:
        return jsonify({"status": "error", "message": msg})

@cores_bp.route('/install-core', methods=['POST'])
def install_core_binaries():
    """دانلود و آپدیت باینری‌های هسته"""
    try:
        CoreInstaller.setup_environment()
        return jsonify({"status": "success", "message": "Core binaries updated successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@cores_bp.route('/add-inbound', methods=['POST'])
def add_inbound():
    """ذخیره اینباند جدید در دیتابیس (فراخوانی از مودال)"""
    try:
        data = request.json
        # تبدیل دیکشنری‌های تودرتو به رشته JSON برای ذخیره در دیتابیس
        # چون در models.py فیلدها Text هستند
        base = data.get('base', {})
        
        new_inbound = Inbound(
            enable=base.get('enabled', True),
            remark=base.get('remark', 'Inbound'),
            protocol=base.get('protocol', 'vless'),
            port=int(base.get('port', 443)),
            listen=base.get('listen', '0.0.0.0'),
            total=int(base.get('total', 0)),
            
            # ذخیره کل تنظیمات به صورت JSON خام
            settings=json.dumps(data.get('settings', {})),
            stream_settings=json.dumps(data.get('stream', {})),
            sniffing=json.dumps(data.get('sniffing', {}))
        )
        
        db.session.add(new_inbound)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Inbound saved to DB."})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})