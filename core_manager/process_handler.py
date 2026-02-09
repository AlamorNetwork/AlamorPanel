import subprocess
import os

class ProcessHandler:
    def __init__(self):
        self.processes = {} # ذخیره PIDها برای مدیریت بعدی

    def start_core(self, core_type, binary_name, config_file):
        # مسیر فایل اجرایی در پوشه bin
        bin_path = os.path.join("bin", binary_name)
        config_path = os.path.join("bin", config_file)
        
        # اگر پروسه قبلاً باز بوده، اول بکشش
        self.stop_core(core_type)

        process = subprocess.Popen(
            [bin_path, "run", "-c", config_file] if "sing" in binary_name else [bin_path, "server", "-c", config_file],
            cwd="bin",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self.processes[core_type] = process
        return process.pid

    def stop_core(self, core_type):
        if core_type in self.processes:
            proc = self.processes[core_type]
            if proc.poll() is None: # اگه هنوز در حال اجراست
                proc.terminate()
            del self.processes[core_type]