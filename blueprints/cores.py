from flask import Blueprint, request, jsonify
from core_manager.config_builder import ConfigBuilder, save_config
from core_manager.process_handler import ProcessHandler

cores_bp = Blueprint('cores', __name__)
handler = ProcessHandler()

@cores_bp.route('/add-inbound', methods=['POST'])
def add_inbound():
    data = request.json
    ptype = data.get('protocol') # sing-box یا hysteria
    port = data.get('port')
    uuid = data.get('uuid')

    if ptype == 'sing-box':
        conf = ConfigBuilder.build_singbox(port, uuid)
        save_config(conf, "sb_config.json")
        pid = handler.start_core("singbox", "sing-box", "sb_config.json")
        return jsonify({"status": "Green", "msg": "Slytherin Power Active", "pid": pid})
    
    return jsonify({"status": "Error", "msg": "Unknown Protocol"})