@echo off
echo === Building Electron App ===
cd /d "%~dp0"

node scripts\verify-dist-for-electron.js
if %errorlevel% neq 0 (
  echo FAILED: dist-backend or frontend/dist incomplete
  exit /b 1
)

cd electron

set CSC_IDENTITY_AUTO_DISCOVERY=false

call npm install
call npx electron-builder --win --dir

echo === Electron build complete: dist-electron\ ===
echo.
echo To run the app, go to: dist-electron\win-unpacked\
echo and launch: "Pipeline Conversion Engine.exe"
