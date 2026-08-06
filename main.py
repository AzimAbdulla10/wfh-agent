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
    Generates a crisp 36x36 px Retina (2x DPI) Menu Bar QIcon:
    - Base: Minimalist Apple-style desktop display outline
    - Badge: Smooth status dot (Apple System Green #34C759 or System Red #FF3B30)
    """
    pixmap = QPixmap(36, 36)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 1. Draw Display Monitor Frame
    monitor_pen = QPen(QColor(52, 56, 60), 1.8)
    monitor_brush = QBrush(QColor(246, 248, 250))
    painter.setPen(monitor_pen)
    painter.setBrush(monitor_brush)
    
    painter.drawRoundedRect(2, 3, 14, 10, 2.0, 2.0)
    
    # Display Stand
    painter.setBrush(QBrush(QColor(52, 56, 60)))
    painter.setPen(Qt.NoPen)
    painter.drawRect(8, 13, 2, 2)
    painter.drawRoundedRect(5, 15, 8, 1.5, 0.5, 0.5)
    
    # 2. Draw Status Indicator Badge
    dot_color = QColor(52, 199, 89) if checked_in else QColor(255, 59, 48)
    
    painter.setPen(QPen(QColor(255, 255, 255), 1.2))
    painter.setBrush(QBrush(dot_color))
    painter.drawEllipse(11, 10, 6.5, 6.5)
    
    painter.end()
    return QIcon(pixmap)


# --- PREMIUM POPPANEL CARD WIDGET ---

class ModernPopoverCard(QWidget):
    """
    Polished macOS Popover Panel Widget inspired by Stats, Ice, and Raycast:
    - Top Header Bar with App Name & Dynamic Status Badge
    - Inset Glassmorphic Info Card with Spacing Rhythm & Icons
    - Prominent Primary Action Card Button with Hover Effects
    - Subtle Footer Controls
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_checked_in = False
        self.init_ui()
        
    def init_ui(self):
        self.setFixedWidth(280)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        
        # 1. HEADER ROW: App Title & Dynamic Status Pill
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.app_title = QLabel("WFH Agent")
        font_title = QFont()
        font_title.setFamilies(["-apple-system", "SF Pro Display", "Helvetica Neue"])
        font_title.setWeight(QFont.Bold)
        font_title.setPointSize(14)
        self.app_title.setFont(font_title)
        self.app_title.setStyleSheet("color: #1D1D1F;")
        
        self.status_pill = QLabel("● CHECKED OUT")
        self.status_pill.setStyleSheet("""
            color: #8E8E93;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
            background-color: rgba(142, 142, 147, 0.15);
            border-radius: 10px;
            padding: 3px 9px;
        """)
        
        header_layout.addWidget(self.app_title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_pill)
        
        # 2. INSET SESSION METADATA CARD
        self.info_card = QFrame()
        self.info_card.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.03);
                border: 1px solid rgba(0, 0, 0, 0.06);
                border-radius: 10px;
            }
        """)
        card_layout = QVBoxLayout(self.info_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)
        
        # Row A: Last Punch
        row_a = QHBoxLayout()
        row_a.setSpacing(6)
        icon_clock = QLabel("🕒")
        icon_clock.setStyleSheet("font-size: 11px; border: none; background: transparent;")
        self.last_punch_label = QLabel("Last Punch: No record")
        self.last_punch_label.setStyleSheet("color: #48484A; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        row_a.addWidget(icon_clock)
        row_a.addWidget(self.last_punch_label)
        row_a.addStretch()
        
        # Row B: Employee ID
        row_b = QHBoxLayout()
        row_b.setSpacing(6)
        icon_user = QLabel("👤")
        icon_user.setStyleSheet("font-size: 11px; border: none; background: transparent;")
        self.emp_id_label = QLabel("Employee ID: --")
        self.emp_id_label.setStyleSheet("color: #8E8E93; font-size: 11px; font-weight: 400; border: none; background: transparent;")
        row_b.addWidget(icon_user)
        row_b.addWidget(self.emp_id_label)
        row_b.addStretch()
        
        card_layout.addLayout(row_a)
        card_layout.addLayout(row_b)
        
        # 3. PROMINENT PRIMARY ACTION BUTTON
        self.action_btn = QPushButton("Check In Now")
        self.action_btn.setFixedHeight(38)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: #FFFFFF;
                font-family: -apple-system, "SF Pro Text", sans-serif;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                padding: 0px 16px;
            }
            QPushButton:hover {
                background-color: #2FB34F;
            }
            QPushButton:pressed {
                background-color: #289E45;
            }
        """)
        self.action_btn.clicked.connect(self.handle_primary_action)
        
        # 4. FOOTER CONTROLS ROW
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(2, 2, 2, 0)
        
        self.logout_btn = QPushButton("Log Out...")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                color: #8E8E93;
                font-size: 11px;
                font-weight: 500;
                border: none;
                background: transparent;
                text-align: left;
            }
            QPushButton:hover {
                color: #1D1D1F;
            }
        """)
        self.logout_btn.clicked.connect(log_out_clicked)
        
        self.quit_btn = QPushButton("Quit Agent")
        self.quit_btn.setCursor(Qt.PointingHandCursor)
        self.quit_btn.setStyleSheet("""
            QPushButton {
                color: #8E8E93;
                font-size: 11px;
                font-weight: 500;
                border: none;
                background: transparent;
                text-align: right;
            }
            QPushButton:hover {
                color: #FF3B30;
            }
        """)
        self.quit_btn.clicked.connect(exit_app)
        
        footer_layout.addWidget(self.logout_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(self.quit_btn)
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.info_card)
        main_layout.addWidget(self.action_btn)
        main_layout.addLayout(footer_layout)
        self.setLayout(main_layout)
        
    def handle_primary_action(self):
        if self.is_checked_in:
            check_out_clicked()
        else:
            check_in_clicked()

    def update_status(self, checked_in, last_log_time=None, last_log_type=None, employee=None):
        self.is_checked_in = checked_in
        
        if checked_in:
            self.status_pill.setText("● WORKING")
            self.status_pill.setStyleSheet("""
                color: #34C759;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
                background-color: rgba(52, 199, 89, 0.15);
                border-radius: 10px;
                padding: 3px 9px;
            """)
            self.action_btn.setText("Check Out")
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF3B30;
                    color: #FFFFFF;
                    font-family: -apple-system, "SF Pro Text", sans-serif;
                    font-size: 13px;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    padding: 0px 16px;
                }
                QPushButton:hover {
                    background-color: #E0332B;
                }
                QPushButton:pressed {
                    background-color: #C22B24;
                }
            """)
            self.logout_btn.setEnabled(False)
            self.logout_btn.setStyleSheet("color: #C7C7CC; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        else:
            self.status_pill.setText("● CHECKED OUT")
            self.status_pill.setStyleSheet("""
                color: #8E8E93;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
                background-color: rgba(142, 142, 147, 0.15);
                border-radius: 10px;
                padding: 3px 9px;
            """)
            self.action_btn.setText("Check In Now")
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34C759;
                    color: #FFFFFF;
                    font-family: -apple-system, "SF Pro Text", sans-serif;
                    font-size: 13px;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    padding: 0px 16px;
                }
                QPushButton:hover {
                    background-color: #2FB34F;
                }
                QPushButton:pressed {
                    background-color: #289E45;
                }
            """)
            self.logout_btn.setEnabled(True)
            self.logout_btn.setStyleSheet("""
                QPushButton {
                    color: #8E8E93;
                    font-size: 11px;
                    font-weight: 500;
                    border: none;
                    background: transparent;
                }
                QPushButton:hover {
                    color: #1D1D1F;
                }
            """)
            
        if last_log_time:
            type_str = f" ({last_log_type})" if last_log_type else ""
            self.last_punch_label.setText(f"Last Punch: {last_log_time}{type_str}")
        else:
            self.last_punch_label.setText("Last Punch: No record")
            
        if employee:
            self.emp_id_label.setText(f"Employee ID: {employee}")
        else:
            self.emp_id_label.setText("Employee ID: Unknown")


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
    
    # 1. Update Modern Popover Card Widget
    if "popover_widget" in globals():
        popover_widget.update_status(checked_in, last_log_time, last_log_type, EMPLOYEE)
    
    # 2. Manage Heartbeat Timer
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
    global tray, popover_widget
    tray = QSystemTrayIcon()
    
    # Set initial dynamic status icon
    initial_status = get_server_status()
    if initial_status is None:
        initial_status = get_local_status()
    tray.setIcon(create_status_icon(initial_status))

    menu = QMenu()
    
    # EMBEDDED MODERN POPOVER CARD WIDGET
    popover_widget = ModernPopoverCard()
    popover_action = QWidgetAction(menu)
    popover_action.setDefaultWidget(popover_widget)
    menu.addAction(popover_action)

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
