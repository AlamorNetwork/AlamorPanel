import json
import uuid
import os

class XrayConfigBuilder:
    
    @staticmethod
    def build_inbound(data):
        """
        تبدیل داده‌های فرم به ساختار استاندارد Inbound مطابق xray.md
        """
        # 1. تنظیمات پایه (Base)
        protocol = data.get('protocol')
        port = int(data.get('port', 443))
        listen = data.get('listen', '0.0.0.0')
        tag = f"inbound-{port}"
        
        inbound = {
            "tag": tag,
            "port": port,
            "listen": listen,
            "protocol": protocol,
            "settings": {},
            "streamSettings": {},
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls", "quic"],
                "routeOnly": False
            }
        }

        # 2. تنظیمات پروتکل (Protocol Settings)
        if protocol == 'vless':
            clients = [{
                "id": data.get('vless_id') or str(uuid.uuid4()),
                "flow": data.get('vless_flow') if data.get('vless_flow') else "",
                "email": data.get('remark', f"user-{port}")
            }]
            inbound['settings'] = {
                "clients": clients,
                "decryption": "none",
                "fallbacks": []
            }
        
        elif protocol == 'vmess':
            inbound['settings'] = {
                "clients": [{
                    "id": data.get('vmess_id') or str(uuid.uuid4()),
                    "alterId": 0,
                    "email": data.get('remark')
                }]
            }
        
        elif protocol == 'trojan':
            inbound['settings'] = {
                "clients": [{
                    "password": data.get('auth_user') or "password",
                    "email": data.get('remark')
                }]
            }
            
        elif protocol == 'shadowsocks':
            inbound['settings'] = {
                "method": data.get('ss_method', 'aes-128-gcm'),
                "password": data.get('ss_password', ''),
                "network": "tcp,udp"
            }
            
        elif protocol == 'dokodemo-door':
            inbound['settings'] = {
                "address": data.get('doko_address', '127.0.0.1'),
                "port": int(data.get('doko_port', 80)),
                "network": data.get('doko_network', 'tcp,udp')
            }
            
        elif protocol == 'wireguard':
            # طبق داکیومنت، وایرگارد تنظیمات استریم ندارد
            inbound['settings'] = {
                "secretKey": data.get('wg_private_key'),
                "peers": json.loads(data.get('wg_peers', '[]')),
                "mtu": int(data.get('wg_mtu', 1420))
            }
            return inbound  # وایرگارد StreamSettings ندارد

        # 3. تنظیمات انتقال (StreamSettings) - بخش کلیدی و پیچیده
        network = data.get('stream_network', 'tcp')
        security = data.get('stream_security', 'none')
        
        stream_settings = {
            "network": network,
            "security": security,
            "sockopt": {
                "mark": int(data.get('tcp_mark', 0)),
                "tcpFastOpen": data.get('tfo') == 'on',
                "tproxy": data.get('tproxy', 'off'),
                "tcpCongestion": data.get('tcp_bbr', 'bbr') if data.get('tcp_bbr') else "bbr",
                "tcpMptcp": data.get('mptcp') == 'on'
            }
        }

        # --- Transport Specifics (جزئیات هر شبکه) ---
        
        # TCP / RAW
        if network == 'tcp' or network == 'raw':
            stream_settings['tcpSettings'] = {
                "header": {"type": "none"}
            }
            
        # WebSocket
        elif network == 'ws':
            stream_settings['wsSettings'] = {
                "path": data.get('trans_path', '/'),
                "headers": {"Host": data.get('trans_host', '')}
            }
            
        # gRPC
        elif network == 'grpc':
            stream_settings['grpcSettings'] = {
                "serviceName": data.get('grpc_service', 'grpc'),
                "multiMode": data.get('grpc_multi') == 'on'
            }
            
        # HTTPUpgrade (New)
        elif network == 'httpupgrade':
            stream_settings['httpupgradeSettings'] = {
                "path": data.get('trans_path', '/'),
                "host": data.get('trans_host', '')
            }
            
        # XHTTP (Beyond Reality - طبق داکیومنت جدید)
        elif network == 'xhttp':
            xhttp_settings = {
                "mode": data.get('xhttp_mode', 'auto'),
                "path": data.get('trans_path', '/'),
                "host": data.get('trans_host', '')
            }
            # اضافه کردن تنظیمات Extra اگر جیسون وارد شده باشد
            if data.get('xhttp_extra'):
                try:
                    extra_json = json.loads(data.get('xhttp_extra'))
                    xhttp_settings['extra'] = extra_json
                except:
                    pass
            stream_settings['xhttpSettings'] = xhttp_settings

        # mKCP
        elif network == 'kcp':
            stream_settings['kcpSettings'] = {
                "mtu": 1350,
                "tti": 50,
                "uplinkCapacity": 50,
                "downlinkCapacity": 100,
                "congestion": True,
                "readBufferSize": 2,
                "writeBufferSize": 2,
                "header": {"type": "none"} # یا wechat-video
            }
            
        # Hysteria (QUIC)
        elif network == 'hysteria':
            stream_settings['hysteriaSettings'] = {
                "up": "100 mbps",
                "down": "100 mbps",
                # طبق داک، پسورد احراز هویت در خود پروتکل نیست، در ترنسپورت است اگر پروتکل VLESS نباشد
                # اما معمولا هیستریا به عنوان پروتکل مستقل استفاده میشه
            }

        # --- Security Specifics (امنیت) ---
        
        if security == 'tls':
            stream_settings['tlsSettings'] = {
                "certificates": [{
                    "certificateFile": data.get('tls_cert'),
                    "keyFile": data.get('tls_key')
                }],
                "alpn": ["h3", "h2", "http/1.1"] if network in ['xhttp', 'hysteria'] else ["h2", "http/1.1"]
            }
            
        elif security == 'reality':
            # تجزیه نام‌های سرور و شناسه کوتاه
            snis = [x.strip() for x in data.get('reality_snis', '').split(',') if x.strip()]
            short_ids = [x.strip() for x in data.get('reality_shortids', '').split(',') if x.strip()]
            
            stream_settings['realitySettings'] = {
                "show": False,
                "dest": data.get('reality_dest', 'google.com:443'),
                "xver": 0,
                "serverNames": snis,
                "privateKey": data.get('reality_key'),
                "shortIds": short_ids,
                "fingerprint": data.get('reality_fingerprint', 'chrome')
            }

        inbound['streamSettings'] = stream_settings
        return inbound

    @staticmethod
    def save_config(inbound_config):
        config_path = '/usr/local/etc/xray/config.json'
        
        # اگر فایل نیست، تمپلیت بساز
        if not os.path.exists(config_path):
            base_config = {
                "log": {"loglevel": "warning"},
                "inbounds": [],
                "outbounds": [{"protocol": "freedom", "tag": "direct"}]
            }
        else:
            try:
                with open(config_path, 'r') as f:
                    base_config = json.load(f)
            except:
                base_config = {"inbounds": [], "outbounds": [{"protocol": "freedom"}]}

        # حذف اینباند تکراری اگر تگ یکسان بود (آپدیت)
        base_config['inbounds'] = [i for i in base_config.get('inbounds', []) if i.get('tag') != inbound_config['tag']]
        
        # افزودن جدید
        base_config['inbounds'].append(inbound_config)
        
        # ذخیره
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(base_config, f, indent=4)
            
        return True