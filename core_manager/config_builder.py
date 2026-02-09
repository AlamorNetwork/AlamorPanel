import json

class ConfigBuilder:
    @staticmethod
    def build_singbox(port, uuid, transport="tcp"):
        """تولید کانفیگ VLESS برای هسته سینگ‌باکس"""
        config = {
            "log": {"level": "info", "timestamp": True},
            "inbounds": [{
                "type": "vless",
                "tag": "vless-in",
                "listen": "::",
                "listen_port": port,
                "users": [{"uuid": uuid}],
                "set_sniffing": True,
                "multiplex": {"enabled": True}
            }],
            "outbounds": [{"type": "direct", "tag": "direct"}]
        }
        return config

    @staticmethod
    def build_hysteria(port, password, cert_path, key_path):
        """تولید کانفیگ برای هسته هیستریا ۲"""
        config = {
            "listen": f":{port}",
            "auth": {"type": "password", "password": password},
            "tls": {
                "cert": cert_path,
                "key": key_path
            },
            "up_mbps": 100,
            "down_mbps": 100
        }
        return config

# این تابع برای ذخیره نهایی فایل استفاده میشه
def save_config(config_dict, filename):
    with open(f"bin/{filename}", "w") as f:
        json.dump(config_dict, f, indent=4)

def build_xray_config(data):
    """
    تبدیل ورودی‌های پنل به فایل config.json برای Xray
    """
    inbound = {
        "port": int(data['port']),
        "protocol": data['protocol'],
        "settings": {
            "clients": [{"id": data['uuid'], "flow": data.get('flow', "")}],
            "decryption": "none"
        },
        "streamSettings": {
            "network": data['network'],
            "security": data['security'],
            f"{data['security']}Settings": {} # تنظیمات TLS یا Reality اینجا پر می‌شود
        },
        "sniffing": {
            "enabled": data.get('sniffing', True),
            "destOverride": ["http", "tls", "quic"]
        }
    }
    return inbound