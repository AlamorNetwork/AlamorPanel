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
    
    @staticmethod
    def setup_environment():
        """ایجاد پوشه‌ها و بررسی وجود هسته‌ها"""
        if not os.path.exists(CoreInstaller.BIN_DIR):
            os.makedirs(CoreInstaller.BIN_DIR)
            print(f"Created bin directory at: {CoreInstaller.BIN_DIR}")

        # بررسی وجود Xray
        if not os.path.exists(CoreInstaller.XRAY_PATH):
            print("Xray core not found. Downloading latest version...")
            CoreInstaller.download_xray()
        else:
            print("Xray core is ready.")

    @staticmethod
    def download_xray():
        """دانلود و استخراج آخرین نسخه Xray-core"""
        try:
            # دریافت آخرین نسخه از گیت‌هاب
            url = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
            response = requests.get(url)
            response.raise_for_status()

            # استخراج فایل زیپ در حافظه
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # استخراج فقط فایل اجرایی xray
                with z.open('xray') as source, open(CoreInstaller.XRAY_PATH, 'wb') as target:
                    shutil.copyfileobj(source, target)
            
            # دادن دسترسی اجرا (chmod +x)
            os.chmod(CoreInstaller.XRAY_PATH, 0o755)
            
            # کپی فایل‌های geo (geoip.dat, geosite.dat)
            # این‌ها برای روتینگ حیاتی هستند
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                for file in ['geoip.dat', 'geosite.dat']:
                    z.extract(file, CoreInstaller.BIN_DIR)

            print("Xray downloaded and installed successfully.")
            return True
        except Exception as e:
            print(f"Failed to download Xray: {e}")
            return False

# برای تست مستقل
if __name__ == "__main__":
    CoreInstaller.setup_environment()