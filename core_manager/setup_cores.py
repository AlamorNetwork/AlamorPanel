import os
import subprocess
import requests
import zipfile
import io
import shutil

class CoreInstaller:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    BIN_DIR = os.path.join(BASE_DIR, 'bin')
    XRAY_PATH = os.path.join(BIN_DIR, 'xray')
    
    # مسیر فایل کانفیگ که Xray باید بخواند (باید با XrayBuilder یکی باشد)
    CONFIG_PATH = "/usr/local/etc/xray/config.json"

    @staticmethod
    def setup_environment():
        """مدیریت کامل: دانلود + نصب سرویس"""
        print(f"Checking Core Environment at {CoreInstaller.BIN_DIR}...")
        
        # 1. ساخت پوشه bin
        if not os.path.exists(CoreInstaller.BIN_DIR):
            os.makedirs(CoreInstaller.BIN_DIR)

        # 2. بررسی فایل باینری
        if not os.path.exists(CoreInstaller.XRAY_PATH):
            print("Xray core missing. Downloading...")
            CoreInstaller.download_xray()
        
        # 3. بررسی و نصب سرویس Systemd (حیاتی برای حل مشکل شما)
        CoreInstaller.install_systemd_service()

    @staticmethod
    def download_xray():
        """دانلود آخرین نسخه Xray"""
        try:
            url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
            print(f"Downloading from {url}...")
            response = requests.get(url)
            response.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                with z.open('xray') as source, open(CoreInstaller.XRAY_PATH, 'wb') as target:
                    shutil.copyfileobj(source, target)
                
                # استخراج فایل‌های Geo
                for file in ['geoip.dat', 'geosite.dat']:
                    try:
                        z.extract(file, CoreInstaller.BIN_DIR)
                    except:
                        pass # اگر نبود مهم نیست

            os.chmod(CoreInstaller.XRAY_PATH, 0o755)
            print("Xray binary downloaded successfully.")
            return True
        except Exception as e:
            print(f"Download Error: {e}")
            return False

    @staticmethod
    def install_systemd_service():
        """ساخت فایل سرویس برای Systemd"""
        service_path = "/etc/systemd/system/xray.service"
        
        # محتوای استاندارد سرویس
        service_content = f"""[Unit]
Description=Xray Service (AlamorHub)
Documentation=https://github.com/xtls
After=network.target nss-lookup.target

[Service]
User=root
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart={CoreInstaller.XRAY_PATH} run -config {CoreInstaller.CONFIG_PATH}
Restart=on-failure
RestartPreventExitStatus=23
LimitNPROC=10000
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
"""
        # اگر سرویس وجود ندارد یا مسیر باینری عوض شده، آن را بازنویسی کن
        needs_update = True
        if os.path.exists(service_path):
            with open(service_path, 'r') as f:
                if CoreInstaller.XRAY_PATH in f.read():
                    needs_update = False
        
        if needs_update:
            print("Installing/Updating Xray Systemd Service...")
            try:
                with open(service_path, 'w') as f:
                    f.write(service_content)
                
                # ریلود کردن دیمن سیستم
                subprocess.run(["systemctl", "daemon-reload"], check=True)
                subprocess.run(["systemctl", "enable", "xray"], check=True)
                print("Xray Service installed and enabled.")
            except Exception as e:
                print(f"Service Install Error (Root required): {e}")

if __name__ == "__main__":
    CoreInstaller.setup_environment()