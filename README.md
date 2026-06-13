# WFH Presence System - Documentation & Handover Guide

This repository contains the **WFH Agent**, a desktop application built with Python (PySide6) designed to track employee presence for work-from-home scenarios. It integrates seamlessly with the **Attendance Analytics** app on a Frappe server.

---

## 🌟 Features

- **Check In / Check Out**: Manual toggles for work status.
- **Heartbeat System**: Sends a pulse every 30 seconds to the server to prove active connection.
- **State Synchronization**: Automatically syncs local UI if the server performs an automatic checkout.
- **Auto-Checkout on Exit**: If the user closes the app while checked in, it attempts to notify the server before quitting.
- **Cross-Platform**: Fully compatible with Linux and Windows.
- **Standalone Packaging**: Optimized for PyInstaller distribution.

---

## 🛠 Project Structure

- `main.py`: The core application code (GUI, API logic, and OS detection).
- `WFH-Agent-Package/`: Contains the **Linux** standalone executable.
- `WFH-Agent-Windows-Kit/`: Contains the **Windows** build script and source files.
- `.gitignore`: Configured to exclude local user data (`config.json`, `status.json`) and build artifacts.

---

## ⚙️ Server-Side Requirements (Frappe)

The agent depends on the **Attendance Analytics** app being installed on the Frappe server.

### 1. API Endpoints
The following whitelisted methods must be available:
- `attendance_analytics.api.checkin`: Logs an 'IN' attendance record.
- `attendance_analytics.api.checkout`: Logs an 'OUT' attendance record.
- `attendance_analytics.api.heartbeat`: Updates the `last_heartbeat` timestamp for an active session.
- `attendance_analytics.api.get_status`: Returns the current server-side check-in status.

### 2. Automatic Checkout (The Scheduler)
For the system to detect disconnected agents, the Frappe scheduler must be running:
- **Task**: `attendance_analytics.tasks.check_missed_heartbeats`
- **Cron**: Should run every 5 minutes (`*/5 * * * *`).
- **Behavior**: If an agent misses heartbeats for >15 minutes, the task creates an 'OUT' record and closes the session.

---

## 🚀 Client Deployment

### For Linux Users
1. Use the file inside `WFH-Agent-Package/`.
2. Run `chmod +x wfh-agent`.
3. Launch the binary. It stores settings in `~/.config/wfh-agent/`.

### For Windows Users
1. Use the `WFH-Agent-Windows-Kit/` folder.
2. Ensure Python is installed and added to PATH.
3. Double-click `build_windows.bat`. This will generate a standalone `.exe` in a `dist/` folder.
4. Settings are stored in `%APPDATA%\wfh-agent\`.

---

## 🔧 Maintenance & Handover Notes

### Data Persistence
- `config.json`: Stores the Server URL and Employee ID.
- `status.json`: Stores a simple boolean `{"checked_in": true/false}` to restore UI state on launch.

### Changing Identity
The **"Log Out"** feature in the tray menu (available only when checked out) will delete the local config files and restart the app, allowing a new user to set it up.

### Troubleshooting
- **Linux UI issues**: If the app won't open, ensure `libxcb-cursor0` is installed (`sudo apt install libxcb-cursor0`).
- **Heartbeat Failures**: Check terminal output; the app prints "Heartbeat sent" and server responses for debugging.

---

*This project was developed for Azim as part of the WFH Presence initiative. For future development, focus on `main.py` for UI/Client changes and the `attendance_analytics` Frappe app for server-side logic.*
