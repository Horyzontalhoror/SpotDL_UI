@echo off
where uv >nul 2>&1
if errorlevel 1 (
    echo uv belum tersedia. Jalankan setup_windows.ps1 terlebih dahulu.
    pause
    exit /b 1
)

uv run app.py
if errorlevel 1 pause
