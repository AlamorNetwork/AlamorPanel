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
    CONFIG_PATH = "/usr/local/etc/xray/config.json"

    @staticmethod
    def setup_environment():
        """مدیریت کامل: دانلود + نصب سرویس (نسخه Force)"""
        print(f"Checking Core Environment at {CoreInstaller.BIN_DIR}...")
        
        # 1. ساخت پوشه bin
        if not os.path.exists(CoreInstaller.BIN_DIR):
            os.makedirs(CoreInstaller.BIN_DIR)

        # 2. دانلود هسته (اگر نباشد یا حجمش صفر باشد)
        if not os.path.exists(CoreInstaller.XRAY_PATH) or os.path.getsize(CoreInstaller.XRAY_PATH) < 1000:
            print("Downloading Xray core...")
            CoreInstaller.download_xray()
        else:
            print("Xray binary found. Skipping download.")
            # اطمینان از دسترسی اجرا
            os.chmod(CoreInstaller.XRAY_PATH, 0o755)

        # 3. نصب اجباری سرویس Systemd
        CoreInstaller.install_systemd_service()

    @staticmethod
    def download_xray():
        try:
            url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
            print(f"Fetching from {url}...")
            response = requests.get(url)
            response.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                with z.open('xray') as source, open(CoreInstaller.XRAY_PATH, 'wb') as target:
                    shutil.copyfileobj(source, target)
                
                for file in ['geoip.dat', 'geosite.dat']:
                    try:
                        z.extract(file, CoreInstaller.BIN_DIR)
                    except:
                        pass

            os.chmod(CoreInstaller.XRAY_PATH, 0o755)
            print("Download complete.")
        except Exception as e:
            print(f"Download Failed: {e}")

    @staticmethod
    def install_systemd_service():
        """ساخت و فعال‌سازی سرویس Xray"""
        service_path = "/etc/systemd/system/xray.service"
        
        service_content = f"""[Unit]
Description=Xray Core Service
Documentation=https://github.com/xtls
After=network.target

[Service]
User=root
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart={CoreInstaller.XRAY_PATH} run -config {CoreInstaller.CONFIG_PATH}
Restart=on-failure
RestartPreventExitStatus=23

[Install]
WantedBy=multi-user.target
"""
        print("Installing Xray Service definition...")
        try:
            # همیشه فایل را بازنویسی کن
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # دستورات سیستمی
            print("Reloading Systemd daemon...")
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            print("Enabling Xray service...")
            subprocess.run(["systemctl", "enable", "xray"], check=True)
            
            print("Starting Xray service...")
            subprocess.run(["systemctl", "restart", "xray"], check=False)
            
            print("✅ Xray Service Successfully Installed & Started!")
            
        except Exception as e:
            print(f"❌ Service Install Error: {e}")

if __name__ == "__main__":
    CoreInstaller.setup_environment()