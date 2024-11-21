import socket  # Thư viện socket để giao tiếp mạng
import json    # Thư viện json để xử lý dữ liệu JSON

SERVER_IP = 'localhost'  # Địa chỉ IP của server
SERVER_PORT = 5555       # Cổng của server

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo một socket TCP/IP
client.connect((SERVER_IP, SERVER_PORT))  # Kết nối đến server qua địa chỉ IP và cổng

token = None  # Biến toàn cục để lưu trữ token sau khi đăng nhập

def send_request(request):
    try:
        client.sendall(json.dumps(request).encode())  # Chuyển đổi request thành JSON và gửi tới server
        data = b""  # Biến để lưu trữ dữ liệu nhận được
        while True:
            part = client.recv(1024)  # Nhận dữ liệu từ server, mỗi lần 1024 byte
            data += part  # Thêm dữ liệu nhận được vào biến data
            if len(part) < 1024:
                break  # Nếu số byte nhận được ít hơn 1024, nghĩa là đã nhận hết dữ liệu
        response = json.loads(data.decode())  # Giải mã dữ liệu từ bytes sang string và chuyển đổi từ JSON sang dictionary
        return response  # Trả về phản hồi từ server
    except ConnectionResetError as e:
        print(f"Error: Connection to the server was lost. {e}")  # Thông báo lỗi nếu mất kết nối với server
        return {"status": "error", "message": "Connection to the server was lost."}  # Trả về thông báo lỗi
    except Exception as e:
        print(f"Unexpected error: {e}")  # Thông báo lỗi không xác định
        return {"status": "error", "message": "Unexpected error occurred."}  # Trả về thông báo lỗi

def register():
    try:
        while True:
            username = input("Enter username: ").strip()  # Yêu cầu người dùng nhập tên đăng nhập và loại bỏ khoảng trắng
            if not username:
                print("Username cannot be empty. Please try again.")  # Kiểm tra tên đăng nhập không được để trống
                continue
            password = input("Enter password: ").strip()  # Yêu cầu người dùng nhập mật khẩu và loại bỏ khoảng trắng
            if not password:
                print("Password cannot be empty. Please try again.")  # Kiểm tra mật khẩu không được để trống
                continue
            break  # Thoát khỏi vòng lặp nếu cả tên đăng nhập và mật khẩu đều hợp lệ
        response = send_request({"action": "register", "username": username, "password": password})  # Gửi yêu cầu đăng ký tới server
        print(response["message"])  # Hiển thị thông báo từ server => chỗ này chỉ hiển thị message không hiển thị status nhé, gọi gì trả nấy !
    except Exception as e:
        print(f"Error during registration: {e}")  # Thông báo lỗi nếu xảy ra trong quá trình đăng ký

def login():
    global token  # Sử dụng biến toàn cục token
    try:
        while True:
            username = input("Enter username: ").strip()  # Yêu cầu người dùng nhập tên đăng nhập
            if not username:
                print("Username cannot be empty. Please try again.")  # Kiểm tra tên đăng nhập không được để trống
                continue
            password = input("Enter password: ").strip()  # Yêu cầu người dùng nhập mật khẩu
            if not password:
                print("Password cannot be empty. Please try again.")  # Kiểm tra mật khẩu không được để trống
                continue
            break  # Thoát khỏi vòng lặp nếu thông tin hợp lệ
        response = send_request({"action": "login", "username": username, "password": password})  # Gửi yêu cầu đăng nhập tới server
        if response["status"] == "success":
            token = response["token"]  # Lưu token nếu đăng nhập thành công
            print("Login successful!")  # Thông báo đăng nhập thành công
        else:
            print(response["message"])  # Hiển thị thông báo lỗi từ server
    except Exception as e:
        print(f"Error during login: {e}")  # Thông báo lỗi nếu xảy ra trong quá trình đăng nhập

def chat():
    if not token:
        print("You need to log in first.")  # Kiểm tra người dùng đã đăng nhập chưa
        return
    try:
        while True:
            message = input("Enter message (or 'exit' to quit): ").strip()  # Yêu cầu nhập tin nhắn
            if not message:
                print("Message cannot be empty. Please try again.")  # Kiểm tra tin nhắn không được để trống
                continue
            if message.lower() == "exit":
                break  # Thoát khỏi chức năng chat nếu người dùng nhập 'exit'
            response = send_request({"action": "chat", "token": token, "message": message})  # Gửi tin nhắn tới server
            print(response["message"])  # Hiển thị phản hồi từ server
    except Exception as e:
        print(f"Error during chat: {e}")  # Thông báo lỗi nếu xảy ra trong quá trình chat

def view_chats():
    if not token:
        print("You need to log in first.")  # Kiểm tra người dùng đã đăng nhập chưa
        return
    try:
        response = send_request({"action": "get_all_chats"})  # Gửi yêu cầu lấy tất cả tin nhắn chat
        for chat in response:
            print(f"{chat['username']} ({chat['timestamp']}): {chat['message']}")  # Hiển thị từng tin nhắn cùng thông tin người gửi và thời gian
    except Exception as e:
        print(f"Error viewing chats: {e}")  # Thông báo lỗi nếu xảy ra trong quá trình xem tin nhắn

def add_project():
    if not token:
        print("You need to log in first.")  # Kiểm tra người dùng đã đăng nhập chưa
        return
    try:
        project_name = input("Enter project name: ").strip()  # Yêu cầu nhập tên dự án
        if not project_name:
            print("Project name cannot be empty. Please try again.")  # Kiểm tra tên dự án không được để trống
            return
        response = send_request({"action": "get_all_users"})  # Gửi yêu cầu lấy danh sách tất cả người dùng
        if response:
            print("\nAvailable users:")
            for user in response:
                print(f"- {user}")  # Hiển thị danh sách người dùng có sẵn
            print("Enter members (comma-separated usernames): ")
            members = input().strip()  # Yêu cầu nhập danh sách thành viên cho dự án
            if not members:
                print("Members cannot be empty. Please try again.")  # Kiểm tra danh sách thành viên không được để trống
                return
            response = send_request({
                "action": "create_project",
                "token": token,
                "project_name": project_name,
                "members": [member.strip() for member in members.split(',')]  # Chuyển đổi danh sách thành viên thành mảng
            })  # Gửi yêu cầu tạo dự án mới tới server
            print(response["message"])  # Hiển thị phản hồi từ server
    except Exception as e:
        print(f"Error adding project: {e}")  # Thông báo lỗi nếu xảy ra trong quá trình thêm dự án

def view_projects():
    try:
        response = send_request({"action": "get_projects"})  # Gửi yêu cầu lấy danh sách các dự án
        if response:
            print("\nProjects:")
            for project in response:
                print(f"ID: {project['id']}, Name: {project['name']}, Owner: {project['owner']}")  # Hiển thị thông tin dự án
                print(f"Members: {', '.join(project['members'])}")  # Hiển thị danh sách thành viên của dự án
        else:
            print("No projects found.")  # Thông báo nếu không có dự án nào
    except Exception as e:
        print(f"Error viewing projects: {e}")  # Thông báo lỗi nếu xảy ra trong quá trình xem dự án

def add_task():
    if not token:
        print("You need to log in first.")  # Kiểm tra người dùng đã đăng nhập chưa
        return
    try:
        project_id = input("Enter project ID: ").strip()  # Yêu cầu nhập ID dự án
        if not project_id.isdigit():
            print("Project ID must be a number. Please try again.")  # Kiểm tra ID dự án phải là số
            return
        project_id = int(project_id)  # Chuyển đổi ID dự án thành số nguyên
        response = send_request({"action": "get_projects"})  # Gửi yêu cầu lấy danh sách các dự án
        if not any(project["id"] == project_id for project in response):
            print(f"Project with ID {project_id} does not exist.")  # Kiểm tra dự án có tồn tại không
            return
        response = send_request({"action": "get_tasks", "project_id": project_id})  # Gửi yêu cầu lấy danh sách công việc của dự án
        print("\nMembers in this project:")
        for project in response:
            print(f"- {project['name']}")  # Hiển thị danh sách thành viên trong dự án
        task_name = input("Enter task name: ").strip()  # Yêu cầu nhập tên công việc
        if not task_name:
            print("Task name cannot be empty. Please try again.")  # Kiểm tra tên công việc không được để trống
            return
        print("Enter task members (comma-separated usernames): ")
        members = input().strip()  # Yêu cầu nhập danh sách thành viên cho công việc
        if not members:
            print("Members cannot be empty. Please try again.")  # Kiểm tra danh sách thành viên không được để trống
            return
        response = send_request({
            "action": "add_task",
            "token": token,
            "project_id": project_id,
            "task_name": task_name,
            "members": [member.strip() for member in members.split(',')]  # Chuyển đổi danh sách thành viên thành mảng
        })  # Gửi yêu cầu thêm công việc mới tới server
        print(response["message"])  # Hiển thị phản hồi từ server
    except Exception as e:
        print(f"Error adding task: {e}")  # Thông báo lỗi nếu xảy ra trong quá trình thêm công việc

def view_tasks():
    try:
        project_id = input("Enter project ID to view tasks: ").strip()  # Yêu cầu nhập ID dự án để xem công việc
        if not project_id.isdigit():
            print("Project ID must be a number. Please try again.")  # Kiểm tra ID dự án phải là số
            return
        project_id = int(project_id)  # Chuyển đổi ID dự án thành số nguyên
        response = send_request({"action": "get_tasks", "project_id": project_id})  # Gửi yêu cầu lấy danh sách công việc của dự án
        if response:
            print("\nTasks:")
            for task in response:
                print(f"Task ID: {task['id']}, Name: {task['name']}")  # Hiển thị thông tin công việc
                print(f"Members: {', '.join(task['members'])}")  # Hiển thị danh sách thành viên của công việc
        else:
            print("No tasks found for this project.")  # Thông báo nếu không có công việc nào
    except Exception as e:
        print(f"Error viewing tasks: {e}")  # Thông báo lỗi nếu xảy ra trong quá trình xem công việc

def main():
    while True:
        print("\n=== MENU ===")  # Hiển thị menu
        print("1. Register")
        print("2. Login")
        print("3. Chat")
        print("4. View Chats")
        print("5. Add Project")
        print("6. View Projects")
        print("7. Add Task")
        print("8. View Tasks")
        print("9. Exit")
        choice = input("Choose an option: ").strip()  # Yêu cầu người dùng chọn một tùy chọn
        if choice == "1":
            register()  # Gọi hàm đăng ký
        elif choice == "2":
            login()  # Gọi hàm đăng nhập
        elif choice == "3":
            chat()  # Gọi hàm chat
        elif choice == "4":
            view_chats()  # Gọi hàm xem tin nhắn
        elif choice == "5":
            add_project()  # Gọi hàm thêm dự án
        elif choice == "6":
            view_projects()  # Gọi hàm xem dự án
        elif choice == "7":
            add_task()  # Gọi hàm thêm công việc
        elif choice == "8":
            view_tasks()  # Gọi hàm xem công việc
        elif choice == "9":
            print("Goodbye!")  # Thông báo tạm biệt
            break  # Thoát khỏi vòng lặp và kết thúc chương trình
        else:
            print("Invalid choice, please try again.")  # Thông báo nếu lựa chọn không hợp lệ

if __name__ == "__main__":
    main()  # Gọi hàm main để bắt đầu chương trình
