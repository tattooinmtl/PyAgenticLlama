@echo off
setlocal enabledelayedexpansion

set MODEL_DIR=%~dp0models
set SERVER=%~dp0llama.cpp\llama-server.exe
set PORT=8080
set CTX=4096

:: Build numbered list of models
set COUNT=0
echo.
echo Available models:
echo.
for %%f in ("%MODEL_DIR%\*.gguf") do (
    set /a COUNT+=1
    set "MODEL_!COUNT!=%%f"
    set "NAME_!COUNT!=%%~nxf"
    echo   [!COUNT!] %%~nxf
)

if %COUNT%==0 (
    echo No .gguf models found in %MODEL_DIR%
    pause
    exit /b 1
)

echo.
set /p CHOICE="Select model [1-%COUNT%]: "

:: Validate input
if "%CHOICE%"=="" goto invalid
if %CHOICE% LSS 1 goto invalid
if %CHOICE% GTR %COUNT% goto invalid

set "MODEL=!MODEL_%CHOICE%!"
set "MODEL_NAME=!NAME_%CHOICE%!"
goto run

:invalid
echo Invalid selection.
pause
exit /b 1

:run
if not exist "%MODEL%" (
    echo Error: model not found at %MODEL%
    pause
    exit /b 1
)

echo.
echo Starting llama-server...
echo   Model : %MODEL_NAME%
echo   Port  : %PORT%
echo.
echo Chat UI : http://localhost:%PORT%
echo API     : http://localhost:%PORT%/v1
echo.
echo Press Ctrl+C to stop.
echo.

"%SERVER%" --model "%MODEL%" --port %PORT% --ctx-size %CTX% --host 0.0.0.0

pause
endlocal
