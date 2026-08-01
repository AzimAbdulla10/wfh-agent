# WFH Agent - Windows Build Kit

This folder contains the build script and documentation to compile the WFH Agent for Windows.

---

## Building on Windows

1. Ensure Python 3 is installed and added to your PATH.
2. Double-click `build_windows.bat` to install dependencies (`PySide6`, `requests`, `pyinstaller`) and generate `dist/wfh-agent.exe`.

---

## Configuration Location

Settings and state are persisted in:
`%APPDATA%\wfh-agent\`
