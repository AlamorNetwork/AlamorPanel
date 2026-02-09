from flask import Blueprint, request, jsonify
from core_manager.config_builder import ConfigBuilder, save_config
from core_manager.process_handler import ProcessHandler
from core_manager.xray_builder import XrayBuilder
from core_manager.setup_cores import CoreInstaller
from database.models import db, Inbound
import json
cores_bp = Blueprint('cores', __name__)
handler = ProcessHandler()



@cores_bp.route('/add-inbound', methods=['POST'])
def add_inbound():
    data = request.json
    
    # ساخت یک رکورد جدید در دیتابیس با تمام جزئیات
    new_inbound = Inbound(
        remark=data['remark'],
        port=int(data['port']),
        protocol=data['protocol'],
        settings=json.dumps(data.get('reality')), # ذخیره تنظیمات به صورت JSON
        stream_settings=json.dumps(data.get('sockopt'))
    )
    
    db.session.add(new_inbound)
    db.session.commit()
    
    return jsonify({"status": "Green", "pid": "Initial-Save-Success"})

@cores_bp.route('/install-core', methods=['POST'])
def install_core_binaries():
    """روت برای دانلود و نصب دستی هسته‌ها"""
    CoreInstaller.setup_environment()
    return jsonify({"status": "success", "message": "Cores checked/installed."})

@cores_bp.route('/restart', methods=['POST'])
def restart_core():
    """اعمال تغییرات و ریستارت سرویس"""
    success, msg = XrayBuilder.apply_config()
    if success:
        return jsonify({"status": "success", "message": msg})
    else:
        return jsonify({"status": "error", "message": msg})