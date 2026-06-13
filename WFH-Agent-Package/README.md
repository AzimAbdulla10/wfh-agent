# WFH Agent - Standalone Linux Package

This folder contains everything needed to run the WFH Agent on a Linux desktop.

## 📦 What's Inside?
- `wfh-agent`: The standalone executable program.

---

## 🚀 Setup Instructions (For the User)

1. **Download**: Move this entire folder to your local machine.
2. **Make it Executable**: Open a terminal in this folder and run:
   ```bash
   chmod +x wfh-agent
   ```
3. **Run**: Double-click the file or run `./wfh-agent` from the terminal.
4. **Configuration**: On the first run, enter your **Server URL** and **Employee ID**.

---

## ⚙️ Server Requirements (For the Admin)

The WFH Agent requires the **Attendance Analytics** app to be installed on your Frappe server.

### 1. Required API Endpoints
The agent calls the following methods in the `attendance_analytics.api` module:
- `checkin`
- `checkout`
- `heartbeat`
- `get_status`

### 2. Mandatory Scheduler (Cron)
For automatic checkouts (when an agent disconnects), the server MUST have the scheduler running.
- **Task**: `attendance_analytics.tasks.check_missed_heartbeats`
- **Recommended Frequency**: Every 5 minutes (`*/5 * * * *`).

Ensure your Frappe bench has the scheduler enabled:
```bash
bench --site [your-site] enable-scheduler
```

---

## 🛠 Troubleshooting

### 1. App won't open (Missing Libraries)
If the app fails to start, you may be missing a core Qt library. Run this command:
```bash
sudo apt update && sudo apt install libxcb-cursor0
```

### 2. Changing Employee ID
To reset the application or switch users:
1. Ensure you are **Checked Out**.
2. Right-click the tray icon and select **Log Out**.
3. The app will restart and ask for new setup details.

### 3. Data Location
The agent stores its local configuration and status in:
`~/.config/wfh-agent/`

---

## 📝 Notes
- **Heartbeat**: The agent sends a pulse every 30 seconds to prove you are online.
- **Auto-Sync**: If you are checked out by the server (e.g., due to a missed heartbeat), the agent will automatically update your local UI and notify you.
