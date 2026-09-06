from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # 當使用者存取網址時，直接回傳 templates/index.html 畫面
    return render_template('index.html')

if __name__ == '__main__':
    # 啟動本地伺服器 (預設 Port: 5000)
    print("🚀 效能測試系統伺服器已啟動！")
    print("👉 請開啟瀏覽器前往：http://127.0.0.1:5000")
    app.run(debug=True, port=5000)