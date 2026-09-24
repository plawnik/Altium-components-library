@echo off
setlocal EnableExtensions
title Altium library - clean source folders

cd /d "%~dp0"

where powershell.exe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Windows PowerShell was not found.
    echo No directories were removed.
    echo.
    pause
    exit /b 1
)

echo Altium source cleanup
echo Repository: %CD%
echo.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\cleanup_source.ps1"
set "CLEANUP_RESULT=%ERRORLEVEL%"

echo.
if "%CLEANUP_RESULT%"=="0" (
    echo Cleanup completed successfully.
) else (
    echo Cleanup did not remove every requested directory.
    echo Read the messages above before closing this window.
)

echo.
pause
exit /b %CLEANUP_RESULT%
