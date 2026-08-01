import requests
import json
import sys
import os

# macOS application support configuration directory
if sys.platform == 'darwin':
    CONFIG_DIR = os.path.expanduser("~/Library/Application Support/wfh-agent")
elif sys.platform == 'win32':
    CONFIG_DIR = os.path.join(os.environ['APPDATA'], 'wfh-agent')
else:
    CONFIG_DIR = os.path.expanduser("~/.config/wfh-agent")

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
STATUS_FILE = os.path.join(CONFIG_DIR, "status.json")

# --- GLOBAL STATE ---
SERVER_URL = None
EMPLOYEE = None
heartbeat_timer = None

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QStyle
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PySide6.QtCore import QTimer, Qt

def create_status_icon(checked_in):
    """
    Generates a high-resolution 32x32 QIcon dynamically:
    - Base: Sleek desktop monitor icon
    - Badge: Green dot (Checked In) or Red dot (Checked Out)
    """
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 1. Draw base monitor screen (Dark Slate outline / light fill)
    monitor_pen = QPen(QColor(50, 54, 58), 2)
    monitor_brush = QBrush(QColor(235, 238, 242))
    painter.setPen(monitor_pen)
    painter.setBrush(monitor_brush)
    
    # Monitor screen rectangle
    painter.drawRoundedRect(3, 4, 22, 15, 3, 3)
    
    # Monitor Stand / Base
    painter.setBrush(QBrush(QColor(50, 54, 58)))
    painter.setPen(Qt.NoPen)
    painter.drawRect(12, 19, 4, 4)
    painter.drawRect(8, 23, 12, 2)
    
    # 2. Draw Status Dot Badge (Bottom-Right corner)
    # Green (#00E676) for Checked In, Red (#FF5252) for Checked Out
    dot_color = QColor(0, 230, 118) if checked_in else QColor(255, 82, 82)
    
    # White border ring for high visibility on macOS dark/light menu bars
    painter.setPen(QPen(QColor(255, 255, 255), 1.5))
    painter.setBrush(QBrush(dot_color))
    painter.drawEllipse(17, 15, 11, 11)
    
    painter.end()
    return QIcon(pixmap)

def get_server_status_details():
    """
    Queries Frappe API for check-in status and last log timestamp.
    Returns dict: {'checked_in': bool, 'last_log_type': str, 'last_log_time': str}
    """
    try:
        response = requests.get(
            f"{SERVER_URL}/api/method/attendance_analytics.api.get_status",
            params={"employee": EMPLOYEE},
            timeout=10
        )
        if response.status_code == 200:
            msg = response.json().get("message", {})
            return {
                "checked_in": msg.get("checked_in", False),
                "last_log_type": msg.get("last_log_type"),
                "last_log_time": str(msg.get("last_log_time", "")).split(".")[0] if msg.get("last_log_time") else None
            }
    except Exception as e:
        print("Error fetching server status:", e)
    return None

def get_server_status():
    info = get_server_status_details()
    return info["checked_in"] if info is not None else None

def get_local_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f:
                return json.load(f).get("checked_in", False)
        except Exception:
            return False
    return False

def save_status(checked_in, last_log_time=None, last_log_type=None):
    data = {"checked_in": checked_in}
    if last_log_time:
        data["last_log_time"] = last_log_time
    if last_log_type:
        data["last_log_type"] = last_log_type
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def sync_ui(checked_in, last_log_time=None, last_log_type=None):
    """Updates Menu Bar Dynamic Icon, Status Indicator, Last Check-in timestamp, and Menu Actions."""
    save_status(checked_in, last_log_time, last_log_type)
    
    # 0. Update Dynamic Menu Bar Tray Icon (Green Dot / Red Dot)
    if "tray" in globals():
        tray.setIcon(create_status_icon(checked_in))
    
    # 1. Update Status Indicator in Context Menu
    if "status_action" in globals():
        if checked_in:
            status_action.setText("🟢 Status: Checked In")
        else:
            status_action.setText("🔴 Status: Checked Out")
            
    # 2. Update Last Check-in timestamp header
    if "last_checkin_action" in globals():
        if last_log_time:
            log_label = f" (Punch: {last_log_type})" if last_log_type else ""
            last_checkin_action.setText(f"Last Log: {last_log_time}{log_label}")
            last_checkin_action.setVisible(True)
        else:
            last_checkin_action.setVisible(False)
            
    # 3. Update Action Buttons & Log Out State
    if "check_in" in globals() and "check_out" in globals():
        check_in.setVisible(not checked_in)
        check_out.setVisible(checked_in)
        
    if "logout_action" in globals():
        logout_action.setEnabled(not checked_in)
    
    # 4. Manage Heartbeat Timer
    if checked_in:
        if heartbeat_timer and not heartbeat_timer.isActive():
            heartbeat_timer.start(30000)
    else:
        if heartbeat_timer and heartbeat_timer.isActive():
            heartbeat_timer.stop()

def fetch_and_sync():
    """Fetches full server status and updates UI."""
    info = get_server_status_details()
    if info is not None:
        sync_ui(info["checked_in"], info.get("last_log_time"), info.get("last_log_type"))
    else:
        sync_ui(get_local_status())

def send_heartbeat():
    try:
        response = requests.post(
            f"{SERVER_URL}/api/method/attendance_analytics.api.heartbeat",
            params={"employee": EMPLOYEE}
        )
        if response.status_code == 200:
            print("Heartbeat sent:", response.text)
            info = get_server_status_details()
            if info is not None:
                if info["checked_in"] is False and get_local_status() is True:
                    sync_ui(False, info.get("last_log_time"), info.get("last_log_type"))
                    if 'tray' in globals():
                        tray.showMessage(
                            "WFH Agent",
                            "You were automatically checked out by the server.",
                            QSystemTrayIcon.Information,
                            3000
                        )
                else:
                    sync_ui(info["checked_in"], info.get("last_log_time"), info.get("last_log_type"))
    except Exception as e:
        print(f"Heartbeat failed: {e}")

def log_out_clicked():
    if heartbeat_timer:
        heartbeat_timer.stop()
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    if os.path.exists(STATUS_FILE):
        os.remove(STATUS_FILE)
    os.execl(sys.executable, sys.executable, *sys.argv)

def load_config():
    global SERVER_URL, EMPLOYEE
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    SERVER_URL = config["server_url"]
    EMPLOYEE = config["employee"]

if os.path.exists(CONFIG_FILE):
    load_config()

class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WFH Agent Setup")
        self.resize(320, 160)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Server URL:"))
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("http://soxo.localhost:8000")
        layout.addWidget(self.server_input)

        layout.addWidget(QLabel("Employee ID:"))
        self.employee_input = QLineEdit()
        self.employee_input.setPlaceholderText("80")
        layout.addWidget(self.employee_input)

        save_button = QPushButton("Save & Start")
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
    fetch_and_sync()
    if 'tray' in globals():
        tray.showMessage("WFH Agent", "Checked In Successfully", QSystemTrayIcon.Information, 3000)

def check_out_clicked():
    try:
        requests.post(
            f"{SERVER_URL}/api/method/attendance_analytics.api.checkout",
            params={"employee": EMPLOYEE}
        )
    except Exception as e:
        print("Check out error:", e)
    fetch_and_sync()
    if 'tray' in globals():
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
    global tray, status_action, last_checkin_action, check_in, check_out, logout_action, exit_action
    tray = QSystemTrayIcon()
    
    # Set initial dynamic status icon
    initial_status = get_server_status()
    if initial_status is None:
        initial_status = get_local_status()
    tray.setIcon(create_status_icon(initial_status))

    menu = QMenu()

    # HEADER INFORMATIONAL ITEMS
    status_action = QAction("🔴 Status: Checked Out")
    status_action.setEnabled(False)
    
    last_checkin_action = QAction("Last Log: Unknown")
    last_checkin_action.setEnabled(False)

    check_in = QAction("Check In")
    check_out = QAction("Check Out")
    logout_action = QAction("Log Out")
    exit_action = QAction("Exit")

    check_in.triggered.connect(check_in_clicked)
    check_out.triggered.connect(check_out_clicked)
    logout_action.triggered.connect(log_out_clicked)
    exit_action.triggered.connect(exit_app)

    # Build Context Menu
    menu.addAction(status_action)
    menu.addAction(last_checkin_action)
    menu.addSeparator()
    menu.addAction(check_in)
    menu.addAction(check_out)
    menu.addSeparator()
    menu.addAction(logout_action)
    menu.addAction(exit_action)

    tray.setContextMenu(menu)
    tray.show()

    # Initial Status Fetch & Sync
    fetch_and_sync()

# --- MAIN EXECUTION ---
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
