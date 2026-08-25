import os
import platform
import psutil
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/specs')
def get_specs():
    # 動態抓取真實系統硬體資訊
    try:
        cpu_name = platform.processor() or "Unknown CPU"
        # 如果 platform 抓不到具體名稱，嘗試用其他方式或預設
        if not cpu_name or cpu_name == "":
            cpu_name = os.cpu_count() and f"Generic CPU ({os.cpu_count()} Cores)" or "Unknown"
        
        physical_cores = psutil.cpu_count(logical=False) or 1
        logical_cores = psutil.cpu_count(logical=True) or 1
        
        # 記憶體資訊
        mem = psutil.virtual_memory()
        total_ram = round(mem.total / (1024 ** 3), 1)
        used_ram = round(mem.used / (1024 ** 3), 1)
        
        os_info = f"{platform.system()} {platform.release()}"

        specs = {
            "cpu_name": f"{cpu_name} (Detected)",
            "cores_threads": f"{physical_cores} 核 / {logical_cores} 線程",
            "memory": f"{used_ram} GB / {total_ram} GB",
            "os": os_info
        }
    except Exception as e:
        specs = {
            "cpu_name": "Intel Core i5 (Fallback)",
            "cores_threads": "6 核 / 6 線程",
            "memory": "16 GB",
            "os": platform.system()
        }

    return jsonify(specs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
