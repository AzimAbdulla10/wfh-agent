import requests
import json
import sys
import os

# --- PATH CONFIGURATION ---
# We store user data in standard OS-specific folders to ensure the 
# app remains portable even when run as a standalone executable.
if sys.platform == 'win32':
    # Windows: %APPDATA%/wfh-agent
    CONFIG_DIR = os.path.join(os.environ['APPDATA'], 'wfh-agent')
else:
    # Linux: ~/.config/wfh-agent
    CONFIG_DIR = os.path.expanduser("~/.config/wfh-agent")

# Ensure the directory exists
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# File paths for configuration and state persistence
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
STATUS_FILE = os.path.join(CONFIG_DIR, "status.json")

# --- GLOBAL STATE ---
SERVER_URL = None
EMPLOYEE = None
heartbeat_timer = None # Managed by QTimer

def send_heartbeat():
    """
    Sends a pulse to the server every 30 seconds to prove the agent is active.
    After each heartbeat, it also fetches server status to ensure local sync.
    """
    try:
        response = requests.post(
            f"{SERVER_URL}/api/method/attendance_analytics.api.heartbeat",
            params={"employee": EMPLOYEE}
        )
        if response.status_code == 200:
            print("Heartbeat sent")
            print(response.text)
            
            # Verify if the server still considers us checked in
            server_status = get_server_status()
            if server_status is False:
                # If server checked us out automatically (e.g. missed pulses), sync local UI
                sync_ui(False)
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
    """Reads the last known check-in state from status.json."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f:
                return json.load(f).get("checked_in", False)
        except Exception:
            return False
    return False

def get_server_status():
    """
    Queries the Frappe API for the actual attendance status.
    The server is ALWAYS the source of truth.
    """
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
    return None # Returns None if unreachable

def log_out_clicked():
    """
    Clears local configuration and identity.
    Only allowed when user is Checked Out.
    Restarts the app to show the Setup Window again.
    """
    if heartbeat_timer:
        heartbeat_timer.stop()
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    if os.path.exists(STATUS_FILE):
        os.remove(STATUS_FILE)
    
    # OS-level restart of the current executable
    os.execl(sys.executable, sys.executable, *sys.argv)

def sync_ui(checked_in):
    """
    Central function to keep UI and background tasks in sync.
    Toggles visibility of Check-in/out buttons and manages the heartbeat timer.
    """
    save_status(checked_in)
    
    # Update Tray Menu Visibility
    if "check_in" in globals() and "check_out" in globals():
        check_in.setVisible(not checked_in)
        check_out.setVisible(checked_in)
    
    # Log Out is only allowed when NOT working
    if "logout_action" in globals():
        logout_action.setEnabled(not checked_in)
    
    # Manage Heartbeat Timer
    if checked_in:
        if heartbeat_timer and not heartbeat_timer.isActive():
            heartbeat_timer.start(30000) # 30 seconds
    else:
        if heartbeat_timer and heartbeat_timer.isActive():
            heartbeat_timer.stop()

def save_status(checked_in):
    """Persists the check-in boolean to status.json."""
    with open(STATUS_FILE, "w") as f:
        json.dump({"checked_in": checked_in}, f)

def load_config():
    """Loads Server URL and Employee ID from config.json into memory."""
    global SERVER_URL, EMPLOYEE
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    SERVER_URL = config["server_url"]
    EMPLOYEE = config["employee"]

# Initial load check
if os.path.exists(CONFIG_FILE):
    load_config()


# --- UI COMPONENTS ---
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QStyle
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QTimer

class SetupWindow(QWidget):
    """The window that appears if no configuration is found."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WFH Agent Setup")
        self.resize(300, 150)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Server URL"))
        self.server_input = QLineEdit()
        layout.addWidget(self.server_input)

        layout.addWidget(QLabel("Employee ID"))
        self.employee_input = QLineEdit()
        layout.addWidget(self.employee_input)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save_config(self):
        config = {
            "server_url": self.server_input.text(),
            "employee": self.employee_input.text()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        load_config()
        self.close()

def check_in_clicked():
    """Handles manual Check In button click."""
    response = requests.post(
        f"{SERVER_URL}/api/method/attendance_analytics.api.checkin",
        params={"employee": EMPLOYEE}
    )
    sync_ui(True)
    tray.showMessage("WFH Agent", "Checked In Successfully", QSystemTrayIcon.Information, 3000)

def check_out_clicked():
    """Handles manual Check Out button click."""
    response = requests.post(
        f"{SERVER_URL}/api/method/attendance_analytics.api.checkout",
        params={"employee": EMPLOYEE}
    )
    sync_ui(False)
    tray.showMessage("WFH Agent", "Checked Out Successfully", QSystemTrayIcon.Information, 3000)

def exit_app():
    """
    Handles application exit. 
    Crucially checks if we should auto-checkout before closing.
    """
    if heartbeat_timer:
        heartbeat_timer.stop()
    
    server_checked_in = get_server_status()
    if server_checked_in is True:
        try:
            # Auto-checkout on exit if still active on server
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

# --- MAIN EXECUTION ---
app = QApplication(sys.argv)

# Initialize background timer
heartbeat_timer = QTimer()
heartbeat_timer.timeout.connect(send_heartbeat)

if not os.path.exists(CONFIG_FILE):
    # FIRST RUN: Show Setup
    setup_window = SetupWindow()
    setup_window.show()
else:
    # SUBSEQUENT RUNS: Start Tray Icon
    tray = QSystemTrayIcon()
    
    # Cross-platform Icon Logic:
    # Try system theme first (Linux), fallback to standard built-in (Windows)
    icon = QIcon.fromTheme("computer")
    if icon.isNull():
        icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
    tray.setIcon(icon)

    menu = QMenu()

    # SYNC STATE WITH SERVER ON STARTUP
    is_checked_in = get_server_status()
    if is_checked_in is None:
        is_checked_in = get_local_status() # Fallback if offline

    # Define Menu Actions
    check_in = QAction("Check In")
    check_out = QAction("Check Out")
    logout_action = QAction("Log Out")
    exit_action = QAction("Exit")

    # Connect Signals
    check_in.triggered.connect(check_in_clicked)
    check_out.triggered.connect(check_out_clicked)
    logout_action.triggered.connect(log_out_clicked)
    exit_action.triggered.connect(exit_app)

    # Build Menu
    menu.addAction(check_in)
    menu.addAction(check_out)
    menu.addSeparator()
    menu.addAction(logout_action)
    menu.addAction(exit_action)

    # Final Setup
    sync_ui(is_checked_in)
    tray.setContextMenu(menu)
    tray.show()

sys.exit(app.exec())
