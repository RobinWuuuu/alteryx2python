@echo off
echo ============================================================
echo   Pipeline Conversion Engine — Full Build
echo ============================================================
echo.

echo [1/3] Building Frontend...
call "%~dp0build-frontend.bat"
if %errorlevel% neq 0 (
    echo FAILED: Frontend build
    exit /b 1
)
echo.

echo [2/3] Building Backend...
call "%~dp0build-backend.bat"
if %errorlevel% neq 0 (
    echo FAILED: Backend build
    exit /b 1
)
echo.

echo [3/3] Building Electron Shell...
call "%~dp0build-electron.bat"
if %errorlevel% neq 0 (
    echo FAILED: Electron build
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD COMPLETE
echo ============================================================
echo.
echo Output: dist-electron\win-unpacked\
echo Launch: "Pipeline Conversion Engine.exe"
echo.
echo To distribute: copy the entire win-unpacked folder
echo to a shared location (SharePoint, network drive, etc.)
echo ============================================================
