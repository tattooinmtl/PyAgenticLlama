@echo off
title PyAgenticLlama
cd /d "%~dp0"
echo.
echo  PyAgenticLlama - Advanced llama.cpp Interface
echo  ========================================
echo.
echo  Installing / updating dependencies...
pip install -r requirements.txt -q
echo  Ready.
echo.
echo  Open http://localhost:7860 in your browser
echo  Press Ctrl+C to stop
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 7860
pause
