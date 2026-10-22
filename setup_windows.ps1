# Menyiapkan seluruh kebutuhan UI SpotDL pada komputer Windows baru.
# Jalankan sekali dari PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1

$ErrorActionPreference = "Stop"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "Windows Package Manager (winget) tidak ditemukan. Instal App Installer dari Microsoft Store, lalu jalankan skrip ini lagi."
}

function Install-WingetPackage([string]$Id) {
    Write-Host "Memastikan $Id tersedia..." -ForegroundColor Cyan
    winget install --id $Id --exact --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "Gagal memasang $Id melalui winget."
    }
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Install-WingetPackage "astral-sh.uv"
}

Install-WingetPackage "Gyan.FFmpeg.Shared"
Install-WingetPackage "DenoLand.Deno"

# Muat kembali PATH agar tool yang baru dipasang dapat dipakai oleh aplikasi
# tanpa perlu menutup jendela PowerShell ini.
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = "$machinePath;$userPath"

Write-Host "Membuat environment Python dan memasang dependensi proyek..." -ForegroundColor Cyan
& uv sync
if ($LASTEXITCODE -ne 0) {
    throw "uv gagal menyiapkan environment proyek."
}

Write-Host "`nSelesai. Jalankan aplikasi dengan: uv run app.py" -ForegroundColor Green
