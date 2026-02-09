import json
import uuid
import os

class XrayConfigBuilder:
    
    @staticmethod
    def build_inbound(data):
        """
        این تابع دیکشنری فرم HTML رو میگیره و اینباند Xray میسازد
        """
        protocol = data.get('protocol')
        port = int(data.get('port', 443))
        remark = data.get('remark', f"User-{port}")
        
        # ساختار پایه اینباند
        inbound = {
            "tag": f"inbound-{port}",
            "port": port,
            "protocol": protocol,
            "settings": {},
            "streamSettings": {
                "network": data.get('network', 'tcp'),
                "security": data.get('security', 'none'),
                "sockopt": {
                    "mark": 0,
                    "tcpFastOpen": True,
                    "tproxy": "off" 
                }
            },
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls", "quic"],
                "routeOnly": True
            }
        }

        # --- 1. تنظیمات پروتکل (SETTINGS) ---
        if protocol == 'vless':
            inbound['settings'] = {
                "clients": [{
                    "id": data.get('vless_id') or str(uuid.uuid4()),
                    "flow": data.get('vless_flow', '')
                }],
                "decryption": "none"
            }
        
        elif protocol == 'vmess':
            inbound['settings'] = {
                "clients": [{
                    "id": data.get('vmess_id') or str(uuid.uuid4()),
                    "alterId": 0
                }]
            }
        
        elif protocol == 'trojan':
            inbound['settings'] = {
                "clients": [{
                    "password": data.get('auth_user') or "password", 
                }]
            }
            
        elif protocol == 'shadowsocks':
            inbound['settings'] = {
                "method": data.get('ss_method'),
                "password": data.get('ss_password'),
                "network": "tcp,udp"
            }

        # --- 2. تنظیمات امنیت (STREAM SETTINGS) ---
        security = data.get('security')
        
        if security == 'tls':
            # نکته مهم SSL: مسیرها باید داینامیک باشن
            # فرض میکنیم کاربر فایل‌ها رو توی مسیر استاندارد Certbot داره
            cert_path = data.get('tls_cert') 
            key_path = data.get('tls_key')
            
            inbound['streamSettings']['tlsSettings'] = {
                "certificates": [{
                    "certificateFile": cert_path,
                    "keyFile": key_path
                }],
                "alpn": ["h2", "http/1.1"]
            }
            
        elif security == 'reality':
            # تنظیمات REALITY که نیاز به دامین واقعی نداره (دزدی دامین!)
            inbound['streamSettings']['realitySettings'] = {
                "show": False,
                "dest": data.get('reality_dest', 'google.com:443'),
                "xver": 0,
                "serverNames": data.get('reality_snis', '').split(','),
                "privateKey": data.get('reality_key'),
                "shortIds": [data.get('reality_shortids', '')]
            }

        # --- 3. تنظیمات انتقال (TRANSPORT) ---
        network = data.get('network')
        
        if network == 'ws':
            inbound['streamSettings']['wsSettings'] = {
                "path": data.get('path', '/'),
                "headers": {"Host": data.get('trans_host', '')}
            }
        
        elif network == 'grpc':
            inbound['streamSettings']['grpcSettings'] = {
                "serviceName": data.get('grpc_service', 'grpc'),
                "multiMode": data.get('grpc_multi') == 'on'
            }
            
        elif network == 'xhttp': # پروتکل جدید Xray
            inbound['streamSettings']['xhttpSettings'] = {
                "mode": data.get('xhttp_mode', 'auto'),
                "path": data.get('path', '/')
            }

        return inbound

    @staticmethod
    def save_config(inbound_config):
        """
        اضافه کردن اینباند جدید به فایل config.json اصلی سرور
        """
        config_path = '/usr/local/etc/xray/config.json' # مسیر پیش‌فرض Xray
        
        # اگر فایل نیست، یک تمپلیت خالی بساز
        if not os.path.exists(config_path):
            base_config = {"inbounds": [], "outbounds": [{"protocol": "freedom"}]}
        else:
            with open(config_path, 'r') as f:
                base_config = json.load(f)

        # اضافه کردن به لیست
        base_config['inbounds'].append(inbound_config)
        
        # ذخیره نهایی
        with open(config_path, 'w') as f:
            json.dump(base_config, f, indent=4)
            
        return True