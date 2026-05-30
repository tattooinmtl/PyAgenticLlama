@echo off
setlocal

set MODEL_DIR=%~dp0models
set SERVER=%~dp0llama.cpp\llama-server.exe
set PORT=8080
set CTX=4096

if not "%~1"=="" (
    set MODEL=%MODEL_DIR%\%~1
    goto run
)

for %%f in ("%MODEL_DIR%\*.gguf") do (
    set MODEL=%%f
    goto run
)

echo No .gguf model found in %MODEL_DIR%
pause
exit /b 1

:run
if not exist "%MODEL%" (
    echo Error: model not found at %MODEL%
    pause
    exit /b 1
)

echo Starting llama-server...
echo   Model : %MODEL%
echo   Port  : %PORT%
echo.
echo Chat UI : http://localhost:%PORT%
echo API     : http://localhost:%PORT%/v1
echo.
echo Press Ctrl+C to stop.
echo.

"%SERVER%" --model "%MODEL%" --port %PORT% --ctx-size %CTX% --host 127.0.0.1 --chat-template llama-3 --instruct
pause
endlocal
