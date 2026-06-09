import requests
import json
import sys
import os

CONFIG_FILE = "config.json"

SERVER_URL = None
EMPLOYEE = None

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    SERVER_URL = config["server_url"]
    EMPLOYEE = config["employee"]


from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton

)

from PySide6.QtGui import QAction, QIcon

class SetupWindow(QWidget):
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

def load_config():
    global SERVER_URL, EMPLOYEE

    with open(CONFIG_FILE) as f:
        config = json.load(f)

    SERVER_URL = config["server_url"]
    EMPLOYEE = config["employee"]

def check_in_clicked():
    response = requests.post(
        f"{SERVER_URL}/api/method/wfh_presence.api.checkin",
        params={
            "employee": EMPLOYEE
        }
    )

    tray.showMessage(
        "WFH Agent",
        "Checked In Successfully",
        QSystemTrayIcon.Information,
        3000
    )


def check_out_clicked():
    response = requests.post(
        f"{SERVER_URL}/api/method/wfh_presence.api.checkout",
        params={
            "employee": EMPLOYEE
        }
    )

    tray.showMessage(
        "WFH Agent",
        "Checked Out Successfully",
        QSystemTrayIcon.Information,
        3000
    )

app = QApplication(sys.argv)

if not os.path.exists(CONFIG_FILE):
    setup_window = SetupWindow()
    setup_window.show()

else:
    tray = QSystemTrayIcon()
    tray.setIcon(QIcon.fromTheme("computer"))

    menu = QMenu()

    check_in = QAction("Check In")
    check_out = QAction("Check Out")
    exit_action = QAction("Exit")

    check_in.triggered.connect(check_in_clicked)
    check_out.triggered.connect(check_out_clicked)

    menu.addAction(check_in)
    menu.addAction(check_out)
    menu.addSeparator()
    menu.addAction(exit_action)

    exit_action.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.show()

sys.exit(app.exec())
