@echo off
title PyAgenticLlama VS Code Extension Installer
echo.
echo  PyAgenticLlama - VS Code Extension Installer
echo  ==============================================
echo.

set VSIX=%~dp0pyagentic-llama-1.0.0.vsix

if not exist "%VSIX%" (
    echo  ERROR: pyagentic-llama-1.0.0.vsix not found next to this script.
    goto :error
)

echo  Installing into VS Code...
call code --install-extension "%VSIX%" --force
if errorlevel 1 ( echo  WARNING: VS Code CLI failed. )

if exist "%USERPROFILE%\.cursor" (
    echo.
    echo  Cursor detected - installing there too...
    call cursor --install-extension "%VSIX%" --force
)

echo.
echo  Done!
echo.
echo  Reload VS Code: Ctrl+Shift+P -^> Developer: Reload Window
echo  Then look for the PyAgenticLlama icon in the left activity bar.
echo.
pause
exit /b 0

:error
echo.
pause
exit /b 1
