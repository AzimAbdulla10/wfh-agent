import requests
import json
import sys
import os

if sys.platform == 'win32':
    CONFIG_DIR = os.path.join(os.environ['APPDATA'], 'wfh-agent')
elif sys.platform == 'darwin':
    CONFIG_DIR = os.path.expanduser("~/Library/Application Support/wfh-agent")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/wfh-agent")

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
STATUS_FILE = os.path.join(CONFIG_DIR, "status.json")

SERVER_URL = None
EMPLOYEE = None
heartbeat_timer = None

def send_heartbeat():
    try:
        response = requests.post(
            f"{SERVER_URL}/api/method/attendance_analytics.api.heartbeat",
            params={"employee": EMPLOYEE}
        )
        if response.status_code == 200:
            print("Heartbeat sent:", response.text)
            server_status = get_server_status()
            if server_status is False:
                sync_ui(False)
                if 'tray' in globals():
                    tray.showMessage(
                        "WFH Agent",
                        "You were automatically checked out by the server.",
                        QSystemTrayIcon.Information,
                        3000
                    )
            elif server_status is True:
                sync_ui(True)
    except Exception as e:
        print(f"Heartbeat failed: {e}")

def get_local_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f:
                return json.load(f).get("checked_in", False)
        except Exception:
            return False
    return False

def get_server_status():
    try:
        response = requests.get(
            f"{SERVER_URL}/api/method/attendance_analytics.api.get_status",
            params={"employee": EMPLOYEE},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("message", {}).get("checked_in", False)
    except Exception:
        pass
    return None

def log_out_clicked():
    if heartbeat_timer:
        heartbeat_timer.stop()
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    if os.path.exists(STATUS_FILE):
        os.remove(STATUS_FILE)
    os.execl(sys.executable, sys.executable, *sys.argv)

def sync_ui(checked_in):
    save_status(checked_in)
    if "check_in" in globals() and "check_out" in globals():
        check_in.setVisible(not checked_in)
        check_out.setVisible(checked_in)
    if "logout_action" in globals():
        logout_action.setEnabled(not checked_in)
    
    if checked_in:
        if heartbeat_timer and not heartbeat_timer.isActive():
            heartbeat_timer.start(30000)
    else:
        if heartbeat_timer and heartbeat_timer.isActive():
            heartbeat_timer.stop()

def save_status(checked_in):
    with open(STATUS_FILE, "w") as f:
        json.dump({"checked_in": checked_in}, f)

def load_config():
    global SERVER_URL, EMPLOYEE
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    SERVER_URL = config["server_url"]
    EMPLOYEE = config["employee"]

if os.path.exists(CONFIG_FILE):
    load_config()

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QStyle
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QTimer

class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WFH Agent Setup")
        self.resize(300, 150)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Server URL"))
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("http://soxo.localhost:8000")
        layout.addWidget(self.server_input)

        layout.addWidget(QLabel("Employee ID"))
        self.employee_input = QLineEdit()
        self.employee_input.setPlaceholderText("80")
        layout.addWidget(self.employee_input)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save_config(self):
        config = {
            "server_url": self.server_input.text().strip(),
            "employee": self.employee_input.text().strip()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        load_config()
        self.close()
        start_tray_app()

def check_in_clicked():
    try:
        requests.post(
            f"{SERVER_URL}/api/method/attendance_analytics.api.checkin",
            params={"employee": EMPLOYEE}
        )
    except Exception as e:
        print("Check in error:", e)
    sync_ui(True)
    tray.showMessage("WFH Agent", "Checked In Successfully", QSystemTrayIcon.Information, 3000)

def check_out_clicked():
    try:
        requests.post(
            f"{SERVER_URL}/api/method/attendance_analytics.api.checkout",
            params={"employee": EMPLOYEE}
        )
    except Exception as e:
        print("Check out error:", e)
    sync_ui(False)
    tray.showMessage("WFH Agent", "Checked Out Successfully", QSystemTrayIcon.Information, 3000)

def exit_app():
    if heartbeat_timer:
        heartbeat_timer.stop()
    server_checked_in = get_server_status()
    if server_checked_in is True:
        try:
            requests.post(
                f"{SERVER_URL}/api/method/attendance_analytics.api.checkout",
                params={"employee": EMPLOYEE},
                timeout=5
            )
            save_status(False)
        except Exception:
            pass
    elif server_checked_in is False:
        save_status(False)
    app.quit()

def start_tray_app():
    global tray, check_in, check_out, logout_action, exit_action
    tray = QSystemTrayIcon()
    icon = QIcon.fromTheme("computer")
    if icon.isNull():
        icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
    tray.setIcon(icon)

    menu = QMenu()
    is_checked_in = get_server_status()
    if is_checked_in is None:
        is_checked_in = get_local_status()

    check_in = QAction("Check In")
    check_out = QAction("Check Out")
    logout_action = QAction("Log Out")
    exit_action = QAction("Exit")

    check_in.triggered.connect(check_in_clicked)
    check_out.triggered.connect(check_out_clicked)
    logout_action.triggered.connect(log_out_clicked)
    exit_action.triggered.connect(exit_app)

    menu.addAction(check_in)
    menu.addAction(check_out)
    menu.addSeparator()
    menu.addAction(logout_action)
    menu.addAction(exit_action)

    sync_ui(is_checked_in)
    tray.setContextMenu(menu)
    tray.show()

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

heartbeat_timer = QTimer()
heartbeat_timer.timeout.connect(send_heartbeat)

if not os.path.exists(CONFIG_FILE):
    setup_window = SetupWindow()
    setup_window.show()
else:
    start_tray_app()

sys.exit(app.exec())
