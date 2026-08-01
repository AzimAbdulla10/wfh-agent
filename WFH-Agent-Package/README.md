# WFH Agent - Standalone Linux Package

This folder contains documentation and files needed to run the WFH Agent on Linux desktops.

---

## Setup Instructions

1. **Make Executable**: Open a terminal in this folder and run:
   ```bash
   chmod +x wfh-agent
   ```
2. **Run**: Launch the binary from the terminal or file manager: `./wfh-agent`.
3. **Configuration**: On initial launch, enter your **Server URL** and **Employee ID**.

---

## System Requirements

- Qt dependencies: If the application fails to start on Ubuntu/Debian, install the required Qt XCB plugin:
  ```bash
  sudo apt update && sudo apt install libxcb-cursor0
  ```

---

## Configuration Location

Configuration files are persisted in:
`~/.config/wfh-agent/`
