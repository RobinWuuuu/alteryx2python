@echo off
echo === Building Frontend ===
cd /d "%~dp0frontend"
call npm install
call npm run build
echo === Frontend build complete: frontend\dist\ ===
