from flask import Flask, render_template, jsonify, Response
import time
import math
import multiprocessing
import concurrent.futures
import psutil
import platform
import json
import winreg
import zlib

app = Flask(__name__)

# --- Geekbench 3 大模擬工作負載 ---
def subtask_compression():
    """1. 檔案壓縮/解壓縮負載 (Compression)"""
    data = b"Geekbench Style Benchmark Task Data " * 50000
    for _ in range(30):
        compressed = zlib.compress(data)
        _ = zlib.decompress(compressed)

def subtask_crypto():
    """2. 加密演算法模擬 (AES/Crypto)"""
    val = 123456789
    for _ in range(1500000):
        val = (val ^ 0x5A5A5A5A) * 1664525 + 1013904223
        val = val & 0xFFFFFFFF

def subtask_matrix():
    """3. 矩陣幾何運算 (Matrix Math)"""
    size = 150
    m1 = [[i + j for j in range(size)] for i in range(size)]
    m2 = [[i * j for j in range(size)] for i in range(size)]
    res = [[0]*size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            res[i][j] = sum(m1[i][k] * m2[k][j] for k in range(size))

def run_geekbench_workload(dummy=None):
    """執行一次完整的 Geekbench 複合工作負載組合"""
    subtask_compression()
    subtask_crypto()
    subtask_matrix()
    return True

# --- 讀取正確 CPU 名稱 ---
def get_clean_cpu_name():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        return cpu_name.strip()
    except Exception:
        return platform.processor() or "Standard CPU"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/system_info')
def system_info():
    return jsonify({
        'cpu_model': get_clean_cpu_name(),
        'cpu_cores': psutil.cpu_count(logical=False) or multiprocessing.cpu_count(),
        'cpu_threads': multiprocessing.cpu_count(),
        'ram_total': f"{round(psutil.virtual_memory().total / (1024**3), 1)} GB",
        'ram_available': f"{round(psutil.virtual_memory().available / (1024**3), 1)} GB",
        'os_system': f"{platform.system()} {platform.release()}"
    })

# 🔥 Geekbench 式：單核基準跑分
# 🔥 5 分鐘 Geekbench 混合任務單核測試
@app.route('/api/run-single-stream')
def run_single_stream():
    def generate():
        target_seconds = 300  # 🎯 鎖定滿滿 300 秒
        start_time = time.perf_counter()
        completed_rounds = 0
        
        while (time.perf_counter() - start_time) < target_seconds:
            run_geekbench_workload()  # 輪流執行 壓縮 + 加密 + 矩陣
            completed_rounds += 1
            
        elapsed = time.perf_counter() - start_time
        # 依據 5 分鐘內完成的總輪數換算分數
        score = int((completed_rounds / elapsed) * 2000)
        
        data = {
            'status': 'completed',
            'single_score': score,
            'single_time': f"{elapsed:.1f} 秒 ({round(elapsed/60, 1)} 分鐘)"
        }
        yield f"data: {json.dumps(data)}\n\n"
        
    return Response(generate(), mimetype='text/event-stream')

# 🔥 5 分鐘 Geekbench 混合任務多核測試
def run_multi_gb_loop(duration_seconds):
    start_time = time.perf_counter()
    rounds = 0
    while (time.perf_counter() - start_time) < duration_seconds:
        run_geekbench_workload()
        rounds += 1
    return rounds

@app.route('/api/run-multi-stream')
def run_multi_stream():
    def generate():
        target_seconds = 300  # 🎯 鎖定滿滿 300 秒
        threads = multiprocessing.cpu_count()
        
        start_time = time.perf_counter()
        with concurrent.futures.ProcessPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(run_multi_gb_loop, target_seconds) for _ in range(threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
        elapsed = time.perf_counter() - start_time
        total_rounds = sum(results)
        
        multi_score = int((total_rounds / elapsed) * 2000 * 0.85)
        
        data = {
            'status': 'completed',
            'multi_score': multi_score,
            'multi_time': f"{elapsed:.1f} 秒 ({round(elapsed/60, 1)} 分鐘)"
        }
        yield f"data: {json.dumps(data)}\n\n"
        
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    multiprocessing.freeze_support()
    app.run(debug=True, port=5000)