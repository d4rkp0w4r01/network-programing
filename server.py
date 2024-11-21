# Import các thư viện cần thiết
import socket  # Thư viện hỗ trợ giao tiếp mạng giữa client và server
import threading  # Thư viện cho phép xử lý nhiều kết nối đồng thời
import logging  # Thư viện ghi lại log hoạt động của server
import os  # Hỗ trợ thao tác với tệp và thư mục
import datetime  # Quản lý thời gian và ngày tháng
import sqlite3  # Cơ sở dữ liệu SQLite để lưu trữ dữ liệu
import json  # Xử lý dữ liệu JSON (gửi/nhận từ client)
from hashlib import sha256  # Thư viện băm mật khẩu để bảo mật
import jwt  # Thư viện tạo và xác thực JSON Web Token (JWT)

# Khởi tạo cơ sở dữ liệu SQLite
def initialize_database():
    conn = sqlite3.connect('db.sqlite3')  # Kết nối hoặc tạo file cơ sở dữ liệu SQLite
    cur = conn.cursor()
    # Tạo bảng người dùng
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,  # Tên người dùng phải là duy nhất
                        password TEXT,  # Lưu mật khẩu (sau khi băm)
                        token TEXT  # Token JWT để xác thực
                    )''')
    # Tạo bảng tin nhắn
    cur.execute('''CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,  # ID người gửi tin nhắn
                        message TEXT,  # Nội dung tin nhắn
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,  # Thời gian gửi tin nhắn
                        FOREIGN KEY(user_id) REFERENCES users(id)  # Khóa ngoại liên kết với bảng users
                    )''')
    # Tạo bảng dự án
    cur.execute('''CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,  # Tên dự án
                        owner INTEGER,  # ID người sở hữu dự án
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  # Thời gian tạo dự án
                        FOREIGN KEY(owner) REFERENCES users(id)  # Khóa ngoại liên kết với bảng users
                    )''')
    # Tạo bảng quản lý thành viên dự án
    cur.execute('''CREATE TABLE IF NOT EXISTS project_members (
                        project_id INTEGER,  # ID dự án
                        user_id INTEGER,  # ID thành viên
                        FOREIGN KEY(project_id) REFERENCES projects(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    # Tạo bảng nhiệm vụ
    cur.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,  # ID dự án chứa nhiệm vụ
                        name TEXT,  # Tên nhiệm vụ
                        FOREIGN KEY(project_id) REFERENCES projects(id)
                    )''')
    # Tạo bảng gán nhiệm vụ cho thành viên
    cur.execute('''CREATE TABLE IF NOT EXISTS task_assignments (
                        task_id INTEGER,  # ID nhiệm vụ
                        user_id INTEGER,  # ID thành viên được gán
                        FOREIGN KEY(task_id) REFERENCES tasks(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    conn.commit()  # Lưu thay đổi vào cơ sở dữ liệu
    conn.close()  # Đóng kết nối cơ sở dữ liệu

# Thiết lập logging cho server
def setup_logging():
    today = datetime.datetime.now().strftime("%d_%m_%Y")  # Lấy ngày hiện tại
    log_dir = f'logs/{today}'  # Thư mục lưu log theo ngày
    os.makedirs(log_dir, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại
    log_file = os.path.join(log_dir, 'server.log')  # Đường dẫn file log
    # Thiết lập cấu hình log
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),  # Ghi log vào file
        logging.StreamHandler()  # Hiển thị log trên console
    ])

# Thiết lập khóa bí mật cho JWT
SECRET_KEY = 'your_secret_key'

# Kết nối cơ sở dữ liệu SQLite
conn = sqlite3.connect('db.sqlite3', check_same_thread=False)  # Cho phép truy cập từ nhiều luồng
cur = conn.cursor()  # Con trỏ để thực thi các truy vấn SQL

# Đăng ký người dùng
def register(username, password):
    hashed_password = sha256(password.encode()).hexdigest()  # Băm mật khẩu
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()  # Lưu thông tin vào cơ sở dữ liệu
        logging.info(f"User registered: {username}")
        return {"status": "success", "message": "User registered successfully"}
    except sqlite3.IntegrityError:  # Lỗi khi tên người dùng đã tồn tại
        return {"status": "error", "message": "Username already exists"}

# Đăng nhập người dùng
def login(username, password):
    hashed_password = sha256(password.encode()).hexdigest()  # Băm mật khẩu
    cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = cur.fetchone()  # Tìm người dùng trong cơ sở dữ liệu
    if user:
        token = jwt.encode({"username": username}, SECRET_KEY, algorithm="HS256")  # Tạo token JWT
        cur.execute("UPDATE users SET token = ? WHERE id = ?", (token, user[0]))
        conn.commit()  # Lưu token vào cơ sở dữ liệu
        logging.info(f"User logged in: {username}")
        return {"status": "success", "token": token}  # Trả token cho client
    else:
        return {"status": "error", "message": "Invalid credentials"}

# Gửi tin nhắn
def chat(token, message):
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # Giải mã token
    username = decoded_token['username']  # Lấy username từ token
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cur.fetchone()  # Lấy ID người dùng từ cơ sở dữ liệu
    if user:
        cur.execute("INSERT INTO chats (user_id, message) VALUES (?, ?)", (user[0], message))  # Lưu tin nhắn
        conn.commit()
        logging.info(f"Message from {username}: {message}")
        return {"status": "success", "message": "Message sent"}
    return {"status": "error", "message": "Authentication failed"}

# Lấy danh sách tin nhắn
def get_all_chats():
    cur.execute("SELECT u.username, c.message, c.timestamp FROM chats c JOIN users u ON c.user_id = u.id ORDER BY c.timestamp")
    chats = cur.fetchall()  # Lấy danh sách tin nhắn
    return [{"username": chat[0], "message": chat[1], "timestamp": chat[2]} for chat in chats]

# Xử lý từng kết nối client
def handle_client(conn, addr):
    with conn:
        logging.info(f"Connected by {addr}")
        while True:
            try:
                data = conn.recv(1024).decode()  # Nhận dữ liệu từ client
                if not data:
                    break  # Ngắt kết nối nếu không nhận được dữ liệu
                request = json.loads(data)  # Phân tích dữ liệu JSON
                action = request.get("action")  # Lấy loại hành động từ yêu cầu
                # Xử lý các hành động từ client
                if action == "register":
                    response = register(request["username"], request["password"])
                elif action == "login":
                    response = login(request["username"], request["password"])
                elif action == "chat":
                    response = chat(request["token"], request["message"])
                elif action == "get_all_chats":
                    response = get_all_chats()
                else:
                    response = {"status": "error", "message": "Invalid action"}
                conn.sendall(json.dumps(response).encode())  # Gửi phản hồi tới client
            except Exception as e:
                logging.error(f"Error: {e}")  # Ghi log lỗi

# Khởi động server
def start_server():
    initialize_database()  # Tạo cơ sở dữ liệu
    setup_logging()  # Thiết lập logging
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo socket TCP
    server.bind(('localhost', 5555))  # Gắn server với địa chỉ và cổng
    server.listen(100)  # Cho phép tối đa 100 kết nối đồng thời
    logging.info("Server is running on port 5555...")
    while True:
        conn, addr = server.accept()  # Chấp nhận kết nối từ client
        threading.Thread(target=handle_client, args=(conn, addr)).start()  # Tạo luồng mới xử lý client

# Điểm bắt đầu chương trình
if __name__ == "__main__":
    start_server()  # Khởi chạy server
