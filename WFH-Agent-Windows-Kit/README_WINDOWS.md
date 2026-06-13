# WFH Agent - Windows Build Kit

This kit allows you to create a Windows version of the WFH Agent.

## 🚀 How to build the .exe (On a Windows PC)

1. **Copy this folder** to a Windows computer.
2. **Double-click** the file named `build_windows.bat`.
3. Wait for the terminal to finish.
4. Your standalone program will be in the new **`dist`** folder named `wfh-agent.exe`.

---

## ⚙️ Server Requirements

The WFH Agent requires the **Attendance Analytics** app to be installed on your Frappe server.

### 1. Required API Endpoints
The agent calls:
- `attendance_analytics.api.checkin`
- `attendance_analytics.api.checkout`
- `attendance_analytics.api.heartbeat`
- `attendance_analytics.api.get_status`

### 2. Mandatory Scheduler (Cron)
The server MUST have the scheduler running every 5 minutes:
`attendance_analytics.tasks.check_missed_heartbeats`

---

## 🛠 Notes for Windows Users

- **Data Location**: Settings are stored in `%APPDATA%\wfh-agent\`.
- **Antivirus**: Some antivirus programs might flag new standalone `.exe` files. If it doesn't open, you may need to "Allow" it or "Run anyway".
- **Icon**: The app uses a standard system "Computer" icon for the tray.
