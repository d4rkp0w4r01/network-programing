# Import thư viện cần thiết
import socket  # Thư viện socket cho giao tiếp TCP/IP
import json  # Thư viện JSON để serialize và deserialize dữ liệu

# Định nghĩa địa chỉ và cổng của server
SERVER_IP = 'localhost'  # Địa chỉ IP server
SERVER_PORT = 5555  # Cổng server

# Tạo socket client và kết nối tới server => Protocol TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

# Biến token toàn cục để lưu trữ token sau khi đăng nhập
token = None

# Hàm gửi yêu cầu đến server
def send_request(request):
    try:
        # Gửi yêu cầu đã được JSON hóa tới server
        client.sendall(json.dumps(request).encode())
        data = b""  # Dữ liệu phản hồi
        while True:
            part = client.recv(1024)  # Nhận dữ liệu từ server
            data += part
            if len(part) < 1024:  # Kiểm tra xem có thêm dữ liệu không
                break
        # Parse dữ liệu nhận được từ server
        response = json.loads(data.decode())
        return response
    except ConnectionResetError as e:
        print(f"Error: Connection to the server was lost. {e}")
        return {"status": "error", "message": "Connection to the server was lost."}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"status": "error", "message": "Unexpected error occurred."}

# Hàm đăng ký người dùng
def register():
    try:
        while True:
            # Nhập tên người dùng
            username = input("Enter username: ").strip()
            if not username:
                print("Username cannot be empty. Please try again.")
                continue
            # Nhập mật khẩu
            password = input("Enter password: ").strip()
            if not password:
                print("Password cannot be empty. Please try again.")
                continue
            break
        # Gửi yêu cầu đăng ký tới server
        response = send_request({"action": "register", "username": username, "password": password})
        print(response["message"])  # Hiển thị kết quả
    except Exception as e:
        print(f"Error during registration: {e}")

# Hàm đăng nhập người dùng
def login():
    global token  # Sử dụng biến token toàn cục
    try:
        while True:
            # Nhập tên người dùng
            username = input("Enter username: ").strip()
            if not username:
                print("Username cannot be empty. Please try again.")
                continue
            # Nhập mật khẩu
            password = input("Enter password: ").strip()
            if not password:
                print("Password cannot be empty. Please try again.")
                continue
            break
        # Gửi yêu cầu đăng nhập tới server
        response = send_request({"action": "login", "username": username, "password": password})
        if response["status"] == "success":
            token = response["token"]  # Lưu token từ phản hồi server
            print("Login successful!")
        else:
            print(response["message"])
    except Exception as e:
        print(f"Error during login: {e}")

# Hàm gửi tin nhắn
def chat():
    if not token:  # Kiểm tra xem người dùng đã đăng nhập chưa
        print("You need to log in first.")
        return
    try:
        while True:
            # Nhập tin nhắn từ người dùng
            message = input("Enter message (or 'exit' to quit): ").strip()
            if not message:
                print("Message cannot be empty. Please try again.")
                continue
            if message.lower() == "exit":  # Thoát khỏi chức năng chat
                break
            # Gửi tin nhắn tới server
            response = send_request({"action": "chat", "token": token, "message": message})
            print(response["message"])
    except Exception as e:
        print(f"Error during chat: {e}")

# Hàm xem danh sách tin nhắn
def view_chats():
    if not token:  # Kiểm tra xem người dùng đã đăng nhập chưa
        print("You need to log in first.")
        return
    try:
        # Gửi yêu cầu xem tin nhắn
        response = send_request({"action": "get_all_chats"})
        # Hiển thị danh sách tin nhắn
        for chat in response:
            print(f"{chat['username']} ({chat['timestamp']}): {chat['message']}")
    except Exception as e:
        print(f"Error viewing chats: {e}")

# Hàm thêm dự án mới
def add_project():
    if not token:  # Kiểm tra xem người dùng đã đăng nhập chưa
        print("You need to log in first.")
        return
    try:
        # Nhập tên dự án
        project_name = input("Enter project name: ").strip()
        if not project_name:
            print("Project name cannot be empty. Please try again.")
            return
        # Gửi yêu cầu để lấy danh sách người dùng
        response = send_request({"action": "get_all_users"})
        if response:
            print("\nAvailable users:")
            for user in response:
                print(f"- {user}")
            # Nhập danh sách thành viên
            print("Enter members (comma-separated usernames): ")
            members = input().strip()
            if not members:
                print("Members cannot be empty. Please try again.")
                return
            # Gửi yêu cầu tạo dự án tới server
            response = send_request({
                "action": "create_project",
                "token": token,
                "project_name": project_name,
                "members": [member.strip() for member in members.split(',')]
            })
            print(response["message"])
    except Exception as e:
        print(f"Error adding project: {e}")

# Hàm xem danh sách dự án
def view_projects():
    try:
        # Gửi yêu cầu xem danh sách dự án
        response = send_request({"action": "get_projects"})
        if response:
            print("\nProjects:")
            # Hiển thị danh sách dự án và thành viên liên quan
            for project in response:
                print(f"ID: {project['id']}, Name: {project['name']}, Owner: {project['owner']}")
                print(f"Members: {', '.join(project['members'])}")
        else:
            print("No projects found.")
    except Exception as e:
        print(f"Error viewing projects: {e}")

# Hàm thêm nhiệm vụ vào dự án
def add_task():
    if not token:  # Kiểm tra xem người dùng đã đăng nhập chưa
        print("You need to log in first.")
        return
    try:
        # Nhập ID dự án
        project_id = input("Enter project ID: ").strip()
        if not project_id.isdigit():
            print("Project ID must be a number. Please try again.")
            return
        project_id = int(project_id)
        # Lấy danh sách dự án
        response = send_request({"action": "get_projects"})
        if not any(project["id"] == project_id for project in response):
            print(f"Project with ID {project_id} does not exist.")
            return
        # Lấy danh sách thành viên
        response = send_request({"action": "get_tasks", "project_id": project_id})
        print("\nMembers in this project:")
        for project in response:
            print(f"- {project['name']}")
        # Nhập tên nhiệm vụ
        task_name = input("Enter task name: ").strip()
        if not task_name:
            print("Task name cannot be empty. Please try again.")
            return
        # Nhập thành viên cho nhiệm vụ
        print("Enter task members (comma-separated usernames): ")
        members = input().strip()
        if not members:
            print("Members cannot be empty. Please try again.")
            return
        # Gửi yêu cầu thêm nhiệm vụ tới server
        response = send_request({
            "action": "add_task",
            "token": token,
            "project_id": project_id,
            "task_name": task_name,
            "members": [member.strip() for member in members.split(',')]
        })
        print(response["message"])
    except Exception as e:
        print(f"Error adding task: {e}")

# Hàm xem danh sách nhiệm vụ
def view_tasks():
    try:
        # Nhập ID dự án để xem nhiệm vụ
        project_id = input("Enter project ID to view tasks: ").strip()
        if not project_id.isdigit():
            print("Project ID must be a number. Please try again.")
            return
        project_id = int(project_id)
        # Gửi yêu cầu lấy danh sách nhiệm vụ
        response = send_request({"action": "get_tasks", "project_id": project_id})
        if response:
            print("\nTasks:")
            # Hiển thị nhiệm vụ và thành viên liên quan
            for task in response:
                print(f"Task ID: {task['id']}, Name: {task['name']}")
                print(f"Members: {', '.join(task['members'])}")
        else:
            print("No tasks found for this project.")
    except Exception as e:
        print(f"Error viewing tasks: {e}")

# Hàm chính chạy chương trình client
def main():
    while True:
        # Menu chức năng
        print("\n=== MENU ===")
        print("1. Register")
        print("2. Login")
        print("3. Chat")
        print("4. View Chats")
        print("5. Add Project")
        print("6. View Projects")
        print("7. Add Task")
        print("8. View Tasks")
        print("9. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            chat()
        elif choice == "4":
            view_chats()
        elif choice == "5":
            add_project()
        elif choice == "6":
            view_projects()
        elif choice == "7":
            add_task()
        elif choice == "8":
            view_tasks()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")

# Điểm bắt đầu của chương trình
if __name__ == "__main__":
    main()
