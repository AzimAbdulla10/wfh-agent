# WFH Agent - macOS Build Kit

This folder contains files to build and deploy the WFH Agent on macOS.

---

## Building and Running on macOS

### 1. Execute Build Script
Open a Terminal in `WFH-Agent-Mac-Kit/` and run:
```bash
./build_mac.sh
```
This installs required dependencies (`PySide6`, `requests`, `pyinstaller`) and compiles `dist/WFH-Agent.app`.

### 2. Configure Auto-Launch at Login
1. Open **System Settings** > **General** > **Login Items**.
2. Under **Open at Login**, select **+** and add `dist/WFH-Agent.app`.

---

## Configuration Location

Configuration and session state are persisted in:
`~/Library/Application Support/wfh-agent/`
