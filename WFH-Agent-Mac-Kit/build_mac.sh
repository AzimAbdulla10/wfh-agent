#!/usr/bin/env bash
set -e

echo "========================================"
echo "WFH Agent - macOS Build Script"
echo "========================================"
echo ""

echo "1. Installing required libraries..."
python3.11 -m pip install PySide6 requests pyinstaller

echo ""
echo "2. Building standalone macOS Application (.app)..."
pyinstaller --windowed --name WFH-Agent main.py

echo ""
echo "========================================"
echo "DONE! Your compiled application is in the 'dist/WFH-Agent.app' folder."
echo "========================================"
