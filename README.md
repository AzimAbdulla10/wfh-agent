# WFH Presence System - Documentation and Setup Guide

This repository contains the **WFH Agent**, a desktop application built with Python (PySide6) designed to track employee presence for work-from-home scenarios. It integrates with a Frappe server running Frappe Framework v15.

---

## Features

- **Check In / Check Out**: Manual toggles for work status.
- **Heartbeat System**: Sends a pulse every 30 seconds to the server to maintain an active connection status.
- **State Synchronization**: Automatically syncs local UI if the server performs an automatic checkout.
- **Auto-Checkout on Exit**: If the user closes the application while checked in, it attempts an automated Checkout API call.
- **Cross-Platform Compatibility**: Fully compatible with Linux, Windows, and macOS.
- **Standalone Packaging**: Optimized for PyInstaller distribution.

---

## Project Structure

- `main.py`: Core application code (GUI, API logic, state persistence, and OS detection).
- `WFH-Agent-Package/`: Contains Linux standalone deployment instructions.
- `WFH-Agent-Windows-Kit/`: Contains Windows build scripts and source files.
- `WFH-Agent-Mac-Kit/`: Contains macOS build scripts and documentation.
- `.gitignore`: Configured to exclude local user data (`config.json`, `status.json`) and build artifacts.

---

## Server-Side Requirements (Frappe)

The agent depends on attendance API endpoints being available on your Frappe server.

### 1. API Endpoints
The following whitelisted methods must be available:
- `/api/method/checkin`: Logs an 'IN' attendance record.
- `/api/method/checkout`: Logs an 'OUT' attendance record.
- `/api/method/heartbeat`: Updates the `last_heartbeat` timestamp for an active session.
- `/api/method/get_status`: Returns current server-side check-in status.

### 2. Automatic Checkout (Scheduler)
For the system to detect disconnected agents, the Frappe scheduler must be active:
- **Behavior**: If an agent misses heartbeats beyond the threshold, the scheduled task creates an 'OUT' record and closes the session.

---

## Client Deployment

### For Linux Users
1. Refer to `WFH-Agent-Package/README.md`.
2. Ensure executable permissions: `chmod +x wfh-agent`.
3. Configuration is saved in `~/.config/wfh-agent/`.

### For Windows Users
1. Refer to `WFH-Agent-Windows-Kit/README_WINDOWS.md`.
2. Run `build_windows.bat` to generate `dist/wfh-agent.exe`.
3. Configuration is saved in `%APPDATA%\wfh-agent\`.

### For macOS Users
1. Refer to `WFH-Agent-Mac-Kit/README_MAC.md`.
2. Run `./build_mac.sh` to generate `dist/WFH-Agent.app`.
3. Configuration is saved in `~/Library/Application Support/wfh-agent/`.

---

## Maintenance Notes

### Data Persistence
- `config.json`: Stores Server URL and Employee ID.
- `status.json`: Stores boolean check-in state (`{"checked_in": true/false}`).

### Changing Identity
The **Log Out** menu option (enabled when checked out) removes local configuration files and restarts the application to allow new user setup.
