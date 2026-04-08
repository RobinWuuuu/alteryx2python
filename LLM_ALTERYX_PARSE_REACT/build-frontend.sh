#!/bin/bash
set -e
echo "=== Building Frontend ==="
cd "$(dirname "$0")/frontend"
npm install
npm run build
echo "=== Frontend build complete: frontend/dist/ ==="
