@echo off
title PyAgenticLlama VS Code Extension Installer
echo.
echo  PyAgenticLlama - VS Code Extension Installer
echo  ==============================================
echo.

set DEST=%USERPROFILE%\.vscode\extensions\pyagentic-llama-1.0.0

echo  Installing to: %DEST%
echo.

if exist "%DEST%" (
    echo  Removing old version...
    rd /s /q "%DEST%"
)

mkdir "%DEST%"
copy "%~dp0package.json" "%DEST%\" >nul
copy "%~dp0extension.js"  "%DEST%\" >nul

echo  Done!
echo.
echo  Next steps:
echo   1. Restart VS Code  (or reload window: Ctrl+Shift+P -> Reload Window)
echo   2. Look for the PyAgenticLlama status bar item at the bottom right
echo   3. Start PyAgenticLlama app, load a model, then send code blocks
echo.
pause
