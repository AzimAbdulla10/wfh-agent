# WFH Agent - macOS Build Kit

This folder contains everything needed to build and run the **WFH Agent** on macOS (Apple Silicon or Intel).

---

## 🚀 How to Build & Run on macOS

### Option 1: Quick Build Script
Open a Terminal in `WFH-Agent-Mac-Kit/` and run:
```bash
./build_mac.sh
```
This script will install `PySide6`, `requests`, and `PyInstaller`, then build a standalone binary in `dist/wfh-agent`.

### Option 2: Manual Build
```bash
python3.11 -m pip install PySide6 requests pyinstaller
pyinstaller --windowed --onefile --name wfh-agent main.py
```

---

## ⚙️ How It Works on macOS

- **Menu Bar Icon**: Runs in the macOS top Menu Bar (system tray).
- **Persistent State**: Stores configuration in `~/Library/Application Support/wfh-agent/config.json`.
- **Automatic Heartbeats**: Sends pulses every 30 seconds while checked in.
- **Graceful Checkout**: Performs an auto-checkout API call if closed while checked in.

---

## 🔧 macOS Permissions & Auto-Start

- **Notifications**: Allow Notifications when prompted on first launch to receive auto-checkout alerts.
- **Start on Login**: To launch automatically when logging into macOS:
  1. Open **System Settings** > **General** > **Login Items**.
  2. Click **+** under *Open at Login* and select the compiled `wfh-agent` app.
