from flask import Blueprint, request, jsonify
from core_manager.config_builder import ConfigBuilder, save_config
from core_manager.process_handler import ProcessHandler
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