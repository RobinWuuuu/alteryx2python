#!/bin/bash
set -e
echo "=== Building Electron App (macOS) ==="
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

node scripts/verify-dist-for-electron.js

cd "$ROOT/electron"

export CSC_IDENTITY_AUTO_DISCOVERY=false

npm install
npx electron-builder --mac --dir

echo "=== Electron build complete: dist-electron/ ==="
echo ""
echo "To run the app, go to: dist-electron/mac-arm64/ (or mac/)"
echo "and open: Pipeline Conversion Engine.app"
