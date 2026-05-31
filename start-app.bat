@echo off
title PyAgenticLlama
cd /d "%~dp0"
echo.
echo  PyAgenticLlama
echo  ================================
echo.
echo  Choose launch mode:
echo.
echo   [1] CPU Only     ^(gpu_layers=0, no Vulkan^)
echo       Best for integrated GPU or low VRAM.
echo       Runs entirely on CPU + RAM. Supports large context.
echo.
echo   [2] Vulkan       ^(gpu_layers=8, AMD/Intel GPU^)
echo       Offloads some layers to GPU via Vulkan.
echo       Works on AMD Radeon, Intel Arc, and most modern GPUs.
echo.
echo   [3] CUDA         ^(gpu_layers=35, NVIDIA GPU^)
echo       Full NVIDIA CUDA acceleration with flash attention.
echo       Requires NVIDIA GPU with 6GB+ VRAM.
echo.
set /p MODE="Select [1/2/3] (default=1): "
if "%MODE%"=="" set MODE=1

if "%MODE%"=="1" goto cpu
if "%MODE%"=="2" goto vulkan
if "%MODE%"=="3" goto cuda
echo Invalid choice, defaulting to CPU Only.
goto cpu

:cpu
echo.
echo  Mode: CPU Only ^(gpu_layers=0, context=16384^)
set LLAMA_BACKEND=cpu
set LLAMA_GPU_LAYERS=0
set LLAMA_FLASH_ATTN=false
set LLAMA_CONTEXT=16384
goto launch

:vulkan
echo.
echo  Mode: Vulkan ^(gpu_layers=8, context=8192^)
set LLAMA_BACKEND=vulkan
set LLAMA_GPU_LAYERS=8
set LLAMA_FLASH_ATTN=false
set LLAMA_CONTEXT=8192
goto launch

:cuda
echo.
echo  Mode: CUDA ^(gpu_layers=35, context=4096, flash_attn=on^)
set LLAMA_BACKEND=cuda
set LLAMA_GPU_LAYERS=35
set LLAMA_FLASH_ATTN=true
set LLAMA_CONTEXT=4096
goto launch

:launch
echo  Installing / updating dependencies...
pip install -r requirements.txt -q
echo  Ready.
echo.
echo  Open http://localhost:7860 in your browser
echo  Press Ctrl+C to stop
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 7860
pause
