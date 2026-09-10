@echo off
title SpotDL Modern GUI
cd /d "%~dp0"

if exist "venv\Scripts\activate" (
    echo Menjalankan dengan Virtual Environment (venv)...
    "venv\Scripts\activate"
    py app.py
) else (
    echo Menjalankan dengan Python sistem...
    py app.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Aplikasi berhenti dengan error (Code %ERRORLEVEL%).
    pause
)
