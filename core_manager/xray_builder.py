import json
import os
import logging
from database.models import Inbound
from core_manager.system_ops import SystemOps
from core_manager.setup_cores import CoreInstaller

# تنظیمات مسیرها
CONFIG_DIR = "/usr/local/etc/xray"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LOG_DIR = "/var/log/xray"

class XrayBuilder:
    """
    موتور تبدیل دیتابیس پنل به کانفیگ استاندارد Xray
    پشتیبانی از: VLESS, VMess, Trojan, SS, WireGuard, Dokodemo
    پشتیبانی از: Reality, TLS, XHTTP, GRPC, WS, TCP
    """
    
    @staticmethod
    def apply_config():
        """
        متد اصلی فراخوانی: ساخت کانفیگ، ذخیره و ریستارت سرویس
        """
        # 1. اطمینان از وجود پوشه‌ها و هسته
        CoreInstaller.setup_environment()
        
        # 2. تولید ساختار کامل کانفیگ
        full_config = XrayBuilder._generate_full_structure()
        
        # 3. ذخیره در فایل
        if not XrayBuilder._write_config_file(full_config):
            return False, "Failed to write config file."
        
        # 4. ریستارت سرویس
        if SystemOps.restart_core_service("xray"):
            return True, "Core reloaded successfully with new config."
        else:
            return False, "Config saved but failed to restart Xray service."

    @staticmethod
    def _generate_full_structure():
        """ساخت اسکلت اصلی JSON"""
        # ساختار پایه
        config = {
            "log": {
                "loglevel": "warning",
                "access": os.path.join(LOG_DIR, "access.log"),
                "error": os.path.join(LOG_DIR, "error.log")
            },
            "api": {
                "tag": "api",
                "services": ["HandlerService", "LoggerService", "StatsService"]
            },
            "stats": {},
            "policy": {
                "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
                "system": {"statsInboundUplink": True, "statsInboundDownlink": True}
            },
            "inbounds": [],
            "outbounds": [
                {"protocol": "freedom", "tag": "direct"},
                {"protocol": "blackhole", "tag": "block"}
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {"type": "field", "inboundTag": ["api"], "outboundTag": "api"}
                ]
            }
        }

        # اضافه کردن API داخلی (برای ارتباط پنل با هسته)
        config["inbounds"].append({
            "tag": "api",
            "port": 10085,
            "listen": "127.0.0.1",
            "protocol": "dokodemo-door",
            "settings": {"address": "127.0.0.1"}
        })

        # دریافت اینباندهای فعال از دیتابیس
        active_inbounds = Inbound.query.filter_by(enable=True).all()
        
        for item in active_inbounds:
            inbound_json = XrayBuilder._build_single_inbound(item)
            if inbound_json:
                config["inbounds"].append(inbound_json)
                # باز کردن پورت در فایروال سیستم
                SystemOps.allow_port(item.port, "tcp") # Xray معمولا روی TCP و UDP با هم کار میکنه
                SystemOps.allow_port(item.port, "udp")

        return config

    @staticmethod
    def _build_single_inbound(item):
        """تبدیل آبجکت دیتابیس به دیکشنری اینباند"""
        try:
            # پارس کردن فیلدهای JSON
            settings = XrayBuilder._parse_json(item.settings)
            stream = XrayBuilder._parse_json(item.stream_settings)
            sniffing = XrayBuilder._parse_json(item.sniffing) or {
                "enabled": True, "destOverride": ["http", "tls", "quic"]
            }

            # ساختار اولیه اینباند
            inbound = {
                "tag": f"inbound-{item.id}",
                "port": item.port,
                "listen": item.listen or "0.0.0.0",
                "protocol": item.protocol,
                "settings": settings,
                "streamSettings": XrayBuilder._clean_stream_settings(stream),
                "sniffing": sniffing
            }
            
            # اصلاحات خاص پروتکل‌ها (Protocol Specific Fixes)
            
            # 1. VLESS / Trojan / VMess -> Clients Array
            if item.protocol in ['vless', 'vmess', 'trojan']:
                # مطمئن شویم آرایه clients وجود دارد (ممکن است در جیسون ذخیره نشده باشد)
                if 'clients' not in settings:
                    # اینجا باید لاجیک ساخت کلاینت دیفالت رو بذاریم اگر خالی بود
                    # اما فرض می‌کنیم که پنل قبلاً این رو درست ذخیره کرده
                    pass

            # 2. VLESS Reality -> Flow fix
            if item.protocol == 'vless' and stream.get('security') == 'reality':
                if not settings.get('decryption'):
                    settings['decryption'] = 'none'

            return inbound

        except Exception as e:
            print(f"Error building inbound {item.id}: {e}")
            return None

    @staticmethod
    def _clean_stream_settings(raw_stream):
        """
        پاکسازی تنظیمات استریم: حذف فیلدهای اضافی که باعث ارور می‌شوند.
        مثلا اگر network=tcp باشد، نباید wsSettings ارسال شود.
        """
        if not raw_stream: return {}
        
        net = raw_stream.get('network', 'tcp')
        sec = raw_stream.get('security', 'none')
        
        clean = {
            "network": net,
            "security": sec,
            "sockopt": raw_stream.get('sockopt', {"mark": 0, "tcpFastOpen": True})
        }

        # نگاشت تنظیمات شبکه
        net_map = {
            'ws': 'wsSettings',
            'grpc': 'grpcSettings',
            'httpupgrade': 'httpUpgradeSettings',
            'xhttp': 'xhttpSettings',
            'kcp': 'kcpSettings',
            'tcp': 'tcpSettings'
        }
        
        if net in net_map and net_map[net] in raw_stream:
            clean[net_map[net]] = raw_stream[net_map[net]]

        # نگاشت تنظیمات امنیت
        sec_map = {
            'tls': 'tlsSettings',
            'reality': 'realitySettings',
            'xtls': 'xtlsSettings'
        }
        
        if sec in sec_map and sec_map[sec] in raw_stream:
            clean[sec_map[sec]] = raw_stream[sec_map[sec]]

        return clean

    @staticmethod
    def _parse_json(data):
        """تبدیل ایمن رشته به دیکشنری"""
        if isinstance(data, dict): return data
        if not data: return {}
        try:
            return json.loads(data)
        except:
            return {}

    @staticmethod
    def _write_config_file(config_data):
        """نوشتن فایل روی دیسک"""
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Write Config Error: {e}")
            return False