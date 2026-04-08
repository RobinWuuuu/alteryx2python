#!/bin/bash
set -e

echo "============================================================"
echo "  Pipeline Conversion Engine — Full Build (macOS)"
echo "============================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/3] Building Frontend..."
bash "$SCRIPT_DIR/build-frontend.sh"
echo ""

echo "[2/3] Building Backend..."
bash "$SCRIPT_DIR/build-backend.sh"
echo ""

echo "[3/3] Building Electron Shell..."
bash "$SCRIPT_DIR/build-electron.sh"

echo ""
echo "============================================================"
echo "  BUILD COMPLETE"
echo "============================================================"
echo ""
echo "Output: dist-electron/mac-arm64/ (Apple Silicon)"
echo "        dist-electron/mac/       (Intel)"
echo ""
echo "Launch: open \"Pipeline Conversion Engine.app\""
echo ""
echo "To distribute: compress the .app bundle into a .zip"
echo "and share via email, SharePoint, or file share."
echo "============================================================"
