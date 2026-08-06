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
    QApplication, QSystemTrayIcon, QMenu, QWidget, QWidgetAction,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QStyle
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont
from PySide6.QtCore import QTimer, Qt

# --- RETINA VECTOR ICON GENERATOR ---

def create_status_icon(checked_in):
    """
    Generates a high-DPI 2x Retina (36x36 px) Menu Bar QIcon:
    - Minimalist desktop display with an embedded status dot
    """
    pixmap = QPixmap(36, 36)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw Display Monitor Frame
    monitor_pen = QPen(QColor(220, 220, 225), 1.8)
    monitor_brush = QBrush(QColor(40, 42, 46))
    painter.setPen(monitor_pen)
    painter.setBrush(monitor_brush)
    
    painter.drawRoundedRect(2, 3, 14, 10, 2.0, 2.0)
    
    # Display Stand
    painter.setBrush(QBrush(QColor(220, 220, 225)))
    painter.setPen(Qt.NoPen)
    painter.drawRect(8, 13, 2, 2)
    painter.drawRoundedRect(5, 15, 8, 1.5, 0.5, 0.5)
    
    # Status Indicator Badge Dot
    dot_color = QColor(52, 199, 89) if checked_in else QColor(255, 59, 48)
    painter.setPen(QPen(QColor(255, 255, 255), 1.2))
    painter.setBrush(QBrush(dot_color))
    painter.drawEllipse(11, 10, 6.5, 6.5)
    
    painter.end()
    return QIcon(pixmap)


def create_action_icon(symbol_type):
    """Generates clean SF Symbol style vector icons for menu actions."""
    pixmap = QPixmap(32, 32)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    if symbol_type == "checkin":
        # Green Circle with White Checkmark
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(52, 199, 89)))
        painter.drawEllipse(1, 1, 14, 14)
        
        pen = QPen(QColor(255, 255, 255), 1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(4.5, 8, 7, 10.5)
        painter.drawLine(7, 10.5, 11.5, 5.5)
        
    elif symbol_type == "checkout":
        # Red Circle with White Cross
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 59, 48)))
        painter.drawEllipse(1, 1, 14, 14)
        
        pen = QPen(QColor(255, 255, 255), 1.8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(5, 5, 11, 11)
        painter.drawLine(11, 5, 5, 11)
        
    elif symbol_type == "logout":
        # Target / Gear circle icon
        pen = QPen(QColor(142, 142, 147), 1.6)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(3, 3, 10, 10)
        painter.drawEllipse(6.5, 6.5, 3, 3)

    elif symbol_type == "exit":
        # Power / Quit Icon
        pen = QPen(QColor(142, 142, 147), 1.8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(3, 3, 10, 10, 40 * 16, 280 * 16)
        painter.drawLine(8, 1, 8, 6.5)
        
    painter.end()
    return QIcon(pixmap)


# --- EXACT MATCH HEADER CARD WIDGET FROM SCREENSHOT ---

class StatusHeaderCard(QWidget):
    """
    Exact Status Header Widget matching the uploaded UI screenshot:
    - Status Dot (🔴 Red for Checked Out, 🟢 Green for Working)
    - Status Title ('Checked Out' in Red / 'Working' in Green)
    - Right-aligned Tag ('ID: 80')
    - Subtitle ('Last Punch: 2026-08-06 22:55:30 (OUT)')
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(6)
        
        # Row 1: Status Dot + Bold Status Title + ID Tag
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.setContentsMargins(0, 0, 0, 0)
        
        self.dot_label = QLabel()
        self.dot_label.setFixedSize(12, 12)
        
        self.status_title = QLabel("Checked Out")
        font_title = QFont()
        font_title.setFamilies(["-apple-system", "SF Pro Text", "Helvetica Neue"])
        font_title.setWeight(QFont.Bold)
        font_title.setPointSize(14)
        self.status_title.setFont(font_title)
        
        row1.addWidget(self.dot_label)
        row1.addWidget(self.status_title)
        row1.addStretch()
        
        # ID Badge Tag (Right Aligned)
        self.emp_tag = QLabel()
        self.emp_tag.setStyleSheet("""
            color: #98989D;
            font-size: 11px;
            font-weight: 600;
            background-color: rgba(255, 255, 255, 0.08);
            border-radius: 5px;
            padding: 3px 8px;
        """)
        row1.addWidget(self.emp_tag)
        
        # Row 2: Secondary Metadata (Last Punch)
        self.subtitle_label = QLabel("Last Punch: No record")
        self.subtitle_label.setStyleSheet("color: #98989D; font-size: 12px; font-weight: 400;")
        
        layout.addLayout(row1)
        layout.addWidget(self.subtitle_label)
        self.setLayout(layout)
        
    def update_status(self, checked_in, last_log_time=None, last_log_type=None, employee=None):
        if checked_in:
            self.dot_label.setStyleSheet("background-color: #34C759; border-radius: 6px;")
            self.status_title.setText("Working")
            self.status_title.setStyleSheet("color: #34C759; font-weight: bold;")
        else:
            self.dot_label.setStyleSheet("background-color: #FF3B30; border-radius: 6px;")
            self.status_title.setText("Checked Out")
            self.status_title.setStyleSheet("color: #FF3B30; font-weight: bold;")
            
        if employee:
            self.emp_tag.setText(f"ID: {employee}")
            self.emp_tag.setVisible(True)
        else:
            self.emp_tag.setVisible(False)
            
        if last_log_time:
            type_str = f" ({last_log_type})" if last_log_type else ""
            self.subtitle_label.setText(f"Last Punch: {last_log_time}{type_str}")
        else:
            self.subtitle_label.setText("Last Punch: No record")


# --- BACKEND API COMMUNICATIONS ---

def get_server_status_details():
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
    save_status(checked_in, last_log_time, last_log_type)
    
    # 0. Update Dynamic Menu Bar Tray Icon
    if "tray" in globals():
        tray.setIcon(create_status_icon(checked_in))
    
    # 1. Update Status Header Card Widget
    if "header_widget" in globals():
        header_widget.update_status(checked_in, last_log_time, last_log_type, EMPLOYEE)
            
    # 2. Update Action Buttons & Log Out State
    if "check_in" in globals() and "check_out" in globals():
        check_in.setVisible(not checked_in)
        check_out.setVisible(checked_in)
        
    if "logout_action" in globals():
        logout_action.setEnabled(not checked_in)
    
    # 3. Manage Heartbeat Timer
    if checked_in:
        if heartbeat_timer and not heartbeat_timer.isActive():
            heartbeat_timer.start(30000)
    else:
        if heartbeat_timer and heartbeat_timer.isActive():
            heartbeat_timer.stop()

def fetch_and_sync():
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


# --- SETUP WINDOW (POLISHED macOS HIG DIALOG) ---

class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WFH Agent Setup")
        self.setFixedSize(340, 210)
        self.setStyleSheet("""
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
                font-size: 13px;
                color: #1D1D1F;
            }
            QLabel {
                font-weight: 500;
                color: #3A3A3C;
            }
            QLineEdit {
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 6px;
                padding: 6px 10px;
                background: #FFFFFF;
                selection-background-color: #007AFF;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
            }
            QPushButton {
                background-color: #007AFF;
                color: #FFFFFF;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0062CC;
            }
            QPushButton:pressed {
                background-color: #004999;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Server URL:"))
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("http://soxo.localhost:8000")
        layout.addWidget(self.server_input)

        layout.addWidget(QLabel("Employee ID:"))
        self.employee_input = QLineEdit()
        self.employee_input.setPlaceholderText("80")
        layout.addWidget(self.employee_input)

        layout.addSpacing(6)
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


# --- TRAY APP INITIALIZATION ---

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
    global tray, header_widget, check_in, check_out, logout_action, exit_action
    tray = QSystemTrayIcon()
    
    # Set initial dynamic status icon
    initial_status = get_server_status()
    if initial_status is None:
        initial_status = get_local_status()
    tray.setIcon(create_status_icon(initial_status))

    menu = QMenu()
    
    # 1. EMBEDDED HEADER CARD (Exact match to screenshot)
    header_widget = StatusHeaderCard()
    header_action = QWidgetAction(menu)
    header_action.setDefaultWidget(header_widget)
    menu.addAction(header_action)
    
    menu.addSeparator()

    # 2. PRIMARY ACTIONS WITH SF SYMBOL ICONS
    check_in = QAction(create_action_icon("checkin"), "Check In", menu)
    check_out = QAction(create_action_icon("checkout"), "Check Out", menu)

    check_in.triggered.connect(check_in_clicked)
    check_out.triggered.connect(check_out_clicked)

    menu.addAction(check_in)
    menu.addAction(check_out)
    
    menu.addSeparator()

    # 3. ACCOUNT & SYSTEM ACTIONS
    logout_action = QAction(create_action_icon("logout"), "Log Out...", menu)
    exit_action = QAction(create_action_icon("exit"), "Quit WFH Agent", menu)

    logout_action.triggered.connect(log_out_clicked)
    exit_action.triggered.connect(exit_app)

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
