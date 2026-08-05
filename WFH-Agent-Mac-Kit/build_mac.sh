#!/bin/bash
set -e

echo "========================================"
echo "WFH Agent macOS Build Script (Optimized)"
echo "========================================"

echo "1. Installing Python dependencies..."
pip install -r requirements.txt

echo "2. Building lightweight macOS Bundle (.app)..."
pyinstaller -y --windowed \
    --name WFH-Agent \
    --exclude-module PySide6.QtPdf \
    --exclude-module PySide6.QtQuick \
    --exclude-module PySide6.QtQml \
    --exclude-module PySide6.QtQmlModels \
    --exclude-module PySide6.Qt3D \
    --exclude-module PySide6.QtWebEngine \
    --exclude-module PySide6.QtVirtualKeyboard \
    --exclude-module PySide6.QtSql \
    --exclude-module PySide6.QtMultimedia \
    --exclude-module PySide6.QtBluetooth \
    --exclude-module PySide6.QtPositioning \
    --exclude-module PySide6.QtSensors \
    --exclude-module PySide6.QtNfc \
    --exclude-module PySide6.QtSpatialAudio \
    --exclude-module PySide6.QtTest \
    --exclude-module PySide6.QtDesigner \
    --exclude-module PySide6.QtHelp \
    --exclude-module setuptools \
    main.py

echo "3. Removing duplicate resources if present..."
rm -rf dist/WFH-Agent.app/Contents/Resources/PySide6 || true

echo ""
echo "========================================"
echo "SUCCESS: App bundle created at 'dist/WFH-Agent.app'"
echo "========================================"
