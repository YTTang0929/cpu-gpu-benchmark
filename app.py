from flask import Flask, render_template, jsonify, Response
import time
import math
import multiprocessing
import concurrent.futures
import psutil
import platform
import json

app = Flask(__name__)

# 取得 CPU 名稱（跨平台安全處理）
def get_clean_cpu_name():
    try:
        if platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            winreg.CloseKey(key)
            return cpu_name.strip()
        else:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
    except Exception:
        pass
    return platform.processor() or "Cloud vCPU"

def subtask_compression(data_chunk):
    compressed = []
    for item in data_chunk:
        h = 0
        for ch in str(item):
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        compressed.append(h)
    return len(compressed)

def run_geekbench_workload(duration=300):
    start_time = time.time()
    total_iterations = 0
    prime_count = 0
    crypto_hash = 0
    compression_count = 0

    chunk_size = 50000
    dummy_data = list(range(chunk_size))

    while time.time() - start_time < duration:
        n = 2000
        for i in range(2, n):
            is_prime = True
            for j in range(2, int(math.isqrt(i)) + 1):
                if i % j == 0:
                    is_prime = False
                    break
            if is_prime:
                prime_count += 1

        val = total_iterations
        for _ in range(500):
            val = ((val * 1103515245 + 12345) & 0x7FFFFFFF)
        crypto_hash ^= val

        compression_count += subtask_compression(dummy_data)
        total_iterations += 1

    return {
        "iterations": total_iterations,
        "primes": prime_count,
        "crypto": crypto_hash,
        "compression": compression_count
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/specs')
def get_specs():
    cores = multiprocessing.cpu_count()
    cpu_name = get_clean_cpu_name()
    return jsonify({
        "cpu_name": cpu_name,
        "cores": cores,
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2)
    })

@app.route('/api/start_stress')
def start_stress():
    def generate():
        cpu_count = multiprocessing.cpu_count()
        duration = 300  # 5 分鐘測試

        yield f"data: {json.dumps({'status': 'starting', 'message': f'啟動 5 分鐘壓力測試 (全速運作 {cpu_count} 核心)...'})}\n\n"

        start_time = time.time()
        with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
            futures = [executor.submit(run_geekbench_workload, duration) for _ in range(cpu_count)]
            
            while True:
                elapsed = time.time() - start_time
                remaining = max(0, duration - elapsed)
                progress = min(100, (elapsed / duration) * 100)
                
                cpu_usage = psutil.cpu_percent(interval=None)
                ram_usage = psutil.virtual_memory().percent

                status_data = {
                    'status': 'running',
                    'progress': round(progress, 1),
                    'elapsed': round(elapsed, 1),
                    'remaining': round(remaining, 1),
                    'cpu_usage': cpu_usage,
                    'ram_usage': ram_usage
                }
                yield f"data: {json.dumps(status_data)}\n\n"

                if elapsed >= duration:
                    break
                time.sleep(1)

            results = [f.result() for f in futures]

        total_iterations = sum(r['iterations'] for r in results)
        total_primes = sum(r['primes'] for r in results)
        total_compression = sum(r['compression'] for r in results)

        score = int((total_iterations * 0.4) + (total_primes * 0.001) + (total_compression * 0.00001))

        final_data = {
            'status': 'completed',
            'score': score,
            'details': {
                'total_iterations': total_iterations,
                'total_primes': total_primes,
                'total_compression': total_compression
            }
        }
        yield f"data: {json.dumps(final_data)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    multiprocessing.freeze_support()
    app.run(host='0.0.0.0', port=5000)
