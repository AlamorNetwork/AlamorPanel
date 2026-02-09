import subprocess
import shutil

class SystemOps:
    @staticmethod
    def check_firewall():
        """بررسی نصب بودن UFW و فعال‌سازی"""
        if not shutil.which("ufw"):
            try:
                subprocess.run(["apt-get", "update"], check=True)
                subprocess.run(["apt-get", "install", "ufw", "-y"], check=True)
            except:
                print("Error installing UFW. Please install manually.")
                return False
        return True

    @staticmethod
    def allow_port(port, protocol='tcp'):
        """باز کردن پورت در فایروال"""
        try:
            # UFW
            subprocess.run(["ufw", "allow", f"{port}/{protocol}"], check=True)
            # IPTABLES (محض اطمینان برای سرورهای خاص)
            subprocess.run(["iptables", "-I", "INPUT", "-p", protocol, "--dport", str(port), "-j", "ACCEPT"], check=False)
            return True
        except Exception as e:
            print(f"Firewall Error: {e}")
            return False

    @staticmethod
    def release_port(port, protocol='tcp'):
        """آزاد کردن پورت (حذف از فایروال)"""
        try:
            subprocess.run(["ufw", "delete", "allow", f"{port}/{protocol}"], check=True)
            # برای iptables کمی پیچیده‌تر است، معمولاً reload کافیست
            return True
        except:
            return False
            
    @staticmethod
    def restart_core_service(service_name="xray"):
        """ریستارت سرویس هسته"""
        try:
            subprocess.run(["systemctl", "restart", service_name], check=True)
            return True
        except:
            return False