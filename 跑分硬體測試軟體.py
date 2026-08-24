import time
import multiprocessing
import cpuinfo
import json
from flask import Flask, render_template, jsonify, Response

app = Flask(__name__)

# ---------------------------------------------------------
# 1. 單核 SSE 測試：拆成 100 等份，實時推送進度 📡
# ---------------------------------------------------------
def generate_single_core():
    start_time = time.time()
    total_iterations = 6500000000  # 65 億次
    steps = 100
    chunk_size = total_iterations // steps

    for progress in range(1, steps + 1):
        # 內層迴圈：跑 1% 的運算量
        for i in range(chunk_size):
            x = i * i

        # 每完成 1%，回傳進度資訊 📊
        data = json.dumps({
            "status": "running",
            "progress": progress
        })
        yield f"data: {data}\n\n"

    # 計算總耗時與分數
    elapsed_time = time.time() - start_time
    score = int((180.0 / elapsed_time) * 1000) if elapsed_time > 0 else 1000

    # 推送 100% 完成狀態與最後結果 🏁
    final_data = json.dumps({
        "status": "completed",
        "progress": 100,
        "single_score": score,
        "single_time": f"{elapsed_time:.2f} 秒"
    })
    yield f"data: {final_data}\n\n"


# ---------------------------------------------------------
# 2. 多核 SSE 測試：同樣拆成 100 等份進行多進程計算 🚀
# ---------------------------------------------------------
def sub_task(iterations):
    for i in range(1, iterations + 1):
        x = i * i

def generate_multi_core():
    start_time = time.time()
    total_iterations = 36000000000  # 360 億次
    num_cores = multiprocessing.cpu_count()
    steps = 100
    chunk_size = (total_iterations // num_cores) // steps

    # 建立進程池
    with multiprocessing.Pool(processes=num_cores) as pool:
        for progress in range(1, steps + 1):
            # 每次讓所有核心並行跑 1% 的工作量
            pool.map(sub_task, [chunk_size] * num_cores)

            # 回傳當前進度 📊
            data = json.dumps({
                "status": "running",
                "progress": progress
            })
            yield f"data: {data}\n\n"

    # 計算總耗時與分數
    elapsed_time = time.time() - start_time
    score = int((120.0 / elapsed_time) * 1000) if elapsed_time > 0 else 1000

    # 推送 100% 完成狀態與最後結果 🏁
    final_data = json.dumps({
        "status": "completed",
        "progress": 100,
        "multi_score": score,
        "multi_time": f"{elapsed_time:.2f} 秒"
    })
    yield f"data: {final_data}\n\n"


# ---------------------------------------------------------
# 路由 (Routes)
# ---------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get-info')
def get_info():
    try:
        info = cpuinfo.get_cpu_info()
        cpu_name = info.get('brand_raw', 'Intel(R) Core(TM) i5-8500 CPU @ 3.00GHz')
    except Exception:
        cpu_name = "Intel(R) Core(TM) i5-8500 CPU @ 3.00GHz"
    
    cores = multiprocessing.cpu_count()
    return jsonify({
        "cpu_name": cpu_name,
        "cores": cores
    })

# 🔑 新增：帶有 SSE 串流的 API 路由
@app.route('/api/run-single-stream')
def run_single_stream():
    return Response(generate_single_core(), content_type='text/event-stream')

@app.route('/api/run-multi-stream')
def run_multi_stream():
    return Response(generate_multi_core(), content_type='text/event-stream')


if __name__ == '__main__':
    multiprocessing.freeze_support()
    app.run(host='127.0.0.1', port=5000, debug=False)