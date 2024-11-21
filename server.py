import socket          # Thư viện socket để tạo kết nối mạng
import threading       # Thư viện threading để xử lý đa luồng
import logging         # Thư viện logging để ghi log
import os              # Thư viện os để tương tác với hệ điều hành
import datetime        # Thư viện datetime để làm việc với thời gian
import sqlite3         # Thư viện sqlite3 để làm việc với cơ sở dữ liệu SQLite
import json            # Thư viện json để xử lý dữ liệu JSON
from hashlib import sha256  # Hàm băm SHA-256 để mã hóa mật khẩu
import jwt             # Thư viện jwt để tạo và xác thực JSON Web Tokens

# Khởi tạo cơ sở dữ liệu
def initialize_database():
    conn = sqlite3.connect('db.sqlite3')  # Kết nối tới cơ sở dữ liệu SQLite, tạo file db.sqlite3 nếu chưa tồn tại
    cur = conn.cursor()  # Tạo một con trỏ để thực thi các câu lệnh SQL

    # Tạo bảng 'users' nếu chưa tồn tại
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        token TEXT
                    )''')
    # Bảng 'users' gồm:
    # - id: khóa chính tự động tăng
    # - username: tên người dùng, phải là duy nhất (UNIQUE)
    # - password: mật khẩu đã được mã hóa
    # - token: JSON Web Token của người dùng

    # Tạo bảng 'chats' để lưu trữ tin nhắn
    cur.execute('''CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    # Bảng 'chats' gồm:
    # - id: khóa chính tự động tăng
    # - user_id: id của người dùng gửi tin nhắn (khóa ngoại tới bảng 'users')
    # - message: nội dung tin nhắn
    # - timestamp: thời gian gửi tin nhắn, mặc định là thời gian hiện tại

    # Tạo bảng 'projects' để lưu trữ dự án
    cur.execute('''CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        owner INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(owner) REFERENCES users(id)
                    )''')
    # Bảng 'projects' gồm:
    # - id: khóa chính tự động tăng
    # - name: tên dự án
    # - owner: id của người tạo dự án (khóa ngoại tới bảng 'users')
    # - created_at: thời gian tạo dự án

    # Tạo bảng 'project_members' để lưu trữ thành viên của dự án
    cur.execute('''CREATE TABLE IF NOT EXISTS project_members (
                        project_id INTEGER,
                        user_id INTEGER,
                        FOREIGN KEY(project_id) REFERENCES projects(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    # Bảng 'project_members' gồm:
    # - project_id: id của dự án (khóa ngoại tới bảng 'projects')
    # - user_id: id của người dùng (khóa ngoại tới bảng 'users')

    # Tạo bảng 'tasks' để lưu trữ công việc
    cur.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        name TEXT,
                        FOREIGN KEY(project_id) REFERENCES projects(id)
                    )''')
    # Bảng 'tasks' gồm:
    # - id: khóa chính tự động tăng
    # - project_id: id của dự án mà công việc thuộc về (khóa ngoại tới bảng 'projects')
    # - name: tên công việc

    # Tạo bảng 'task_assignments' để lưu trữ việc phân công công việc cho người dùng
    cur.execute('''CREATE TABLE IF NOT EXISTS task_assignments (
                        task_id INTEGER,
                        user_id INTEGER,
                        FOREIGN KEY(task_id) REFERENCES tasks(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    # Bảng 'task_assignments' gồm:
    # - task_id: id của công việc (khóa ngoại tới bảng 'tasks')
    # - user_id: id của người dùng (khóa ngoại tới bảng 'users')

    conn.commit()  # Lưu các thay đổi vào cơ sở dữ liệu
    conn.close()   # Đóng kết nối với cơ sở dữ liệu

# Thiết lập logging
def setup_logging():
    today = datetime.datetime.now().strftime("%d_%m_%Y")  # Lấy ngày hiện tại dưới dạng chuỗi 'dd_mm_yyyy'
    log_dir = f'logs/{today}'  # Đường dẫn thư mục log theo ngày
    os.makedirs(log_dir, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại
    log_file = os.path.join(log_dir, 'server.log')  # Đường dẫn file log
    logging.basicConfig(
        level=logging.INFO,  # Thiết lập mức độ ghi log là INFO
        format='%(asctime)s - %(message)s',  # Định dạng log bao gồm thời gian và thông báo
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),  # Ghi log vào file với mã hóa utf-8
            logging.StreamHandler()  # Hiển thị log ra console
        ]
    )

# Các hàm xử lý
SECRET_KEY = 'your_secret_key'  # Khóa bí mật để mã hóa JWT
conn = sqlite3.connect('db.sqlite3', check_same_thread=False)  # Kết nối tới cơ sở dữ liệu, cho phép đa luồng truy cập
cur = conn.cursor()  # Tạo con trỏ để thực thi SQL

def register(username, password):
    hashed_password = sha256(password.encode()).hexdigest()  # Mã hóa mật khẩu bằng SHA-256
    try:
        # Thêm người dùng mới vào bảng 'users'
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        # Giải thích:
        # - Sử dụng câu lệnh INSERT để thêm bản ghi mới vào bảng 'users'
        # - Các giá trị được truyền vào thông qua tuple (username, hashed_password)
        # - Dấu '?' là placeholder để ngăn chặn SQL Injection => liên quan đến bảo mật chỗ này không quan trọng

        conn.commit()  # Lưu thay đổi vào cơ sở dữ liệu
        logging.info(f"User registered: {username}")  # Ghi log thông báo người dùng đã đăng ký
        return {"status": "success", "message": "User registered successfully"}  # Trả về phản hồi thành công => hiển thị bên client message
    except sqlite3.IntegrityError:
        return {"status": "error", "message": "Username already exists"}  # Thông báo lỗi nếu tên đăng nhập đã tồn tại

def login(username, password):
    hashed_password = sha256(password.encode()).hexdigest()  # Mã hóa mật khẩu nhập vào
    # Kiểm tra thông tin đăng nhập trong cơ sở dữ liệu
    cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    # Giải thích:
    # - Sử dụng câu lệnh SELECT để truy vấn người dùng với username và password đã mã hóa
    # - Nếu tìm thấy bản ghi khớp, người dùng tồn tại và thông tin đăng nhập đúng

    user = cur.fetchone()  # Lấy bản ghi đầu tiên khớp với thông tin
    if user:
        token = jwt.encode({"username": username}, SECRET_KEY, algorithm="HS256")
        # Tạo JWT chứa tên người dùng
        # Cập nhật token vào cơ sở dữ liệu cho người dùng
        cur.execute("UPDATE users SET token = ? WHERE id = ?", (token, user[0]))
        # Giải thích:
        # - Sử dụng câu lệnh UPDATE để cập nhật cột 'token' của người dùng
        # - 'user[0]' là 'id' của người dùng trong kết quả truy vấn

        conn.commit()  # Lưu thay đổi
        logging.info(f"User logged in: {username}")  # Ghi log người dùng đã đăng nhập
        return {"status": "success", "token": token}  # Trả về token cho client
    else:
        return {"status": "error", "message": "Invalid credentials"}  # Thông báo lỗi nếu thông tin đăng nhập không đúng

def chat(token, message):
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    # Giải mã token để lấy thông tin người dùng
    username = decoded_token['username']  # Lấy tên người dùng từ token
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    # Giải thích:
    # - Truy vấn id của người dùng dựa trên username
    # - Sử dụng câu lệnh SELECT để lấy 'id' từ bảng 'users'

    user = cur.fetchone()
    if user:
        cur.execute("INSERT INTO chats (user_id, message) VALUES (?, ?)", (user[0], message))
        # Giải thích:
        # - Chèn tin nhắn mới vào bảng 'chats' với 'user_id' và 'message'
        # - 'user[0]' là 'id' của người dùng

        conn.commit()  # Lưu thay đổi
        logging.info(f"Message from {username}: {message}")  # Ghi log tin nhắn
        return {"status": "success", "message": "Message sent"}  # Phản hồi thành công => hiển thị bên client message
    return {"status": "error", "message": "Authentication failed"}  # Thông báo lỗi nếu xác thực thất bại

def get_all_chats():
    cur.execute("""
        SELECT u.username, c.message, c.timestamp
        FROM chats c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.timestamp
    """)
    # Giải thích:
    # - Sử dụng câu lệnh SELECT với JOIN để kết hợp bảng 'chats' và 'users'
    # - Lấy 'username', 'message', 'timestamp' của tất cả tin nhắn
    # - Sắp xếp kết quả theo 'timestamp'

    chats = cur.fetchall()  # Lấy tất cả các bản ghi
    return [{"username": chat[0], "message": chat[1], "timestamp": chat[2]} for chat in chats]
    # Trả về danh sách tin nhắn dưới dạng dictionary

def create_project(token, project_name, members):
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    # Giải mã token để lấy thông tin người dùng
    username = decoded_token['username']
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    # Truy vấn id của chủ sở hữu dự án

    owner = cur.fetchone()
    if owner:
        cur.execute("INSERT INTO projects (name, owner) VALUES (?, ?)", (project_name, owner[0]))
        # Giải thích:
        # - Thêm dự án mới vào bảng 'projects' với 'name' và 'owner'
        # - 'owner[0]' là 'id' của chủ sở hữu dự án

        project_id = cur.lastrowid  # Lấy id của dự án vừa tạo
        for member in members:
            cur.execute("SELECT id FROM users WHERE username = ?", (member,))
            # Truy vấn id của từng thành viên dựa trên username
            user = cur.fetchone()
            if user:
                cur.execute("INSERT INTO project_members (project_id, user_id) VALUES (?, ?)", (project_id, user[0]))
                # Giải thích:
                # - Thêm mỗi thành viên vào bảng 'project_members' với 'project_id' và 'user_id'

        conn.commit()  # Lưu thay đổi
        logging.info(f"Project created: {project_name} by {username} with members {members}")
        # Ghi log thông tin dự án được tạo
        return {"status": "success", "message": "Project created successfully"}  # Phản hồi thành công => hiển thị bên client message
    return {"status": "error", "message": "Invalid token"}  # Thông báo lỗi nếu token không hợp lệ

def add_task(token, project_id, task_name, members):
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    # Giải mã token để lấy tên người dùng
    username = decoded_token['username']
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    # Truy vấn id của người dùng hiện tại

    user = cur.fetchone()
    if user:
        cur.execute("SELECT owner FROM projects WHERE id = ?", (project_id,))
        # Truy vấn 'owner' của dự án dựa trên 'project_id'
        project_owner = cur.fetchone()
        if project_owner and project_owner[0] == user[0]:
            # Kiểm tra xem người dùng có phải là chủ sở hữu của dự án không

            cur.execute("INSERT INTO tasks (project_id, name) VALUES (?, ?)", (project_id, task_name))
            # Giải thích:
            # - Thêm công việc mới vào bảng 'tasks' với 'project_id' và 'name'

            task_id = cur.lastrowid  # Lấy id của công việc vừa tạo
            for member in members:
                cur.execute("SELECT id FROM users WHERE username = ?", (member,))
                # Truy vấn id của thành viên được gán công việc
                assigned_user = cur.fetchone()
                if assigned_user:
                    cur.execute("INSERT INTO task_assignments (task_id, user_id) VALUES (?, ?)", (task_id, assigned_user[0]))
                    # Giải thích:
                    # - Gán công việc cho thành viên trong bảng 'task_assignments'

            conn.commit()  # Lưu thay đổi
            logging.info(f"Task '{task_name}' added to project {project_id} by {username}")
            # Ghi log thông tin công việc được thêm
            return {"status": "success", "message": "Task added successfully"}  # Phản hồi thành công => hiển thị bên client message
    return {"status": "error", "message": "Only project owner can add tasks"}  # Thông báo lỗi nếu không phải chủ sở hữu dự án

def get_projects():
    cur.execute("""
        SELECT p.id, p.name, u.username
        FROM projects p
        JOIN users u ON p.owner = u.id
    """)
    # Giải thích:
    # - Sử dụng JOIN để kết hợp bảng 'projects' và 'users'
    # - Lấy 'id', 'name' của dự án và 'username' của chủ sở hữu

    projects = cur.fetchall()
    result = []
    for proj in projects:
        cur.execute("""
            SELECT u.username
            FROM project_members pm
            JOIN users u ON pm.user_id = u.id
            WHERE pm.project_id = ?
        """, (proj[0],))
        # Giải thích:
        # - Lấy danh sách thành viên của dự án bằng cách JOIN 'project_members' và 'users'
        # - Lọc theo 'project_id'

        members = [member[0] for member in cur.fetchall()]
        result.append({"id": proj[0], "name": proj[1], "owner": proj[2], "members": members})
        # Thêm thông tin dự án vào danh sách kết quả
    return result  # Trả về danh sách các dự án

def get_tasks(project_id):
    cur.execute("SELECT id, name FROM tasks WHERE project_id = ?", (project_id,))
    # Giải thích:
    # - Lấy danh sách công việc của dự án dựa trên 'project_id'

    tasks = cur.fetchall()
    result = []
    for task in tasks:
        cur.execute("""
            SELECT u.username
            FROM task_assignments ta
            JOIN users u ON ta.user_id = u.id
            WHERE ta.task_id = ?
        """, (task[0],))
        # Giải thích:
        # - Lấy danh sách thành viên được gán cho công việc bằng cách JOIN 'task_assignments' và 'users'
        # - Lọc theo 'task_id'

        members = [member[0] for member in cur.fetchall()]
        result.append({"id": task[0], "name": task[1], "members": members})
        # Thêm thông tin công việc vào danh sách kết quả
    return result  # Trả về danh sách công việc

def get_all_users():
    cur.execute("SELECT username FROM users")
    # Giải thích:
    # - Lấy danh sách tất cả người dùng từ bảng 'users'

    users = [user[0] for user in cur.fetchall()]
    return users  # Trả về danh sách tên người dùng

# Xử lý từng kết nối client
def handle_client(conn, addr):
    with conn:
        logging.info(f"Connected by {addr}")  # Ghi log khi có kết nối mới
        while True:
            try:
                data = conn.recv(1024).decode()  # Nhận dữ liệu từ client và giải mã
                if not data:
                    break  # Thoát nếu không nhận được dữ liệu
                request = json.loads(data)  # Chuyển đổi dữ liệu từ JSON sang dictionary
                action = request.get("action")  # Lấy hành động từ yêu cầu
                # Xử lý các hành động từ client
                if action == "register":
                    response = register(request["username"], request["password"])
                elif action == "login":
                    response = login(request["username"], request["password"])
                elif action == "chat":
                    response = chat(request["token"], request["message"])
                elif action == "get_all_chats":
                    response = get_all_chats()
                elif action == "create_project":
                    response = create_project(request["token"], request["project_name"], request["members"])
                elif action == "add_task":
                    response = add_task(request["token"], request["project_id"], request["task_name"], request["members"])
                elif action == "get_projects":
                    response = get_projects()
                elif action == "get_tasks":
                    response = get_tasks(request["project_id"])
                elif action == "get_all_users":
                    response = get_all_users()
                else:
                    response = {"status": "error", "message": "Invalid action"}  # Thông báo lỗi nếu hành động không hợp lệ
                conn.sendall(json.dumps(response).encode())  # Gửi phản hồi tới client
            except ConnectionResetError as e:
                logging.error(f"ConnectionResetError: {e} - Client {addr} disconnected.")  # Ghi log nếu kết nối bị ngắt
                break
            except json.JSONDecodeError as e:
                logging.error(f"JSONDecodeError: {e} - Invalid data from {addr}.")  # Ghi log nếu dữ liệu không hợp lệ
            except Exception as e:
                logging.error(f"Error: {e}")  # Ghi log các lỗi khác

# Chạy server
def start_server():
    initialize_database()  # Khởi tạo cơ sở dữ liệu
    setup_logging()        # Thiết lập logging
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo một socket TCP/IP
    server.bind(('localhost', 5555))  # Gắn socket vào địa chỉ và cổng
    server.listen(100)  # Lắng nghe tối đa 100 kết nối
    logging.info("Server is running on port 5555...")  # Ghi log thông báo server đang chạy
    while True:
        conn, addr = server.accept()  # Chấp nhận kết nối từ client
        threading.Thread(target=handle_client, args=(conn, addr)).start()  # Tạo một luồng mới để xử lý client

if __name__ == "__main__":
    start_server()  # Gọi hàm start_server để bắt đầu chạy server
