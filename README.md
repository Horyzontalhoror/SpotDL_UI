# SpotDL Modern GUI Downloader

Aplikasi antarmuka desktop modern (GUI) berbasis **PyQt6** dan **pyqtdarktheme** untuk mengunduh lagu dan playlist Spotify serta YouTube dengan metadata lengkap via **SpotDL**.

## ✨ Fitur Utama

### 1. 📥 Tab Download & Antrean (Queue)
- **Multi-Link Input**: Paste banyak link sekaligus (1 link per baris). Mendukung link Spotify, YouTube, atau kombinasi `YouTubeURL|SpotifyURL`.
- **Tabel Antrean Terstruktur**: Menampilkan kolom nomor urut `#`, tipe link, URL, dan status (`⏳ Menunggu`, `🔄 Mengunduh...`, `✅ Selesai`, `❌ Gagal`, `⏹ Dibatalkan`).
- **Urutan Unduhan Cerdas**:
  - **Abaikan yang Sudah Selesai**: Tombol *▶ Download Semua Antrean* hanya memproses item yang berstatus `Menunggu` atau `Gagal`, secara otomatis melewati link yang sudah `Selesai`.
  - **Download Item Terpilih**: Tombol *🎯 Download Item Terpilih* memungkinkan Anda memilih satu atau beberapa baris tertentu saja untuk diunduh.
  - **Reset Status Gagal**: Tombol *🔄 Reset Status Gagal* untuk mencoba kembali semua unduhan yang error dengan sekali klik.
  - **Manajemen Antrean**: Tombol *🗑 Hapus Terpilih* dan *🧹 Hapus Selesai*.
- **Live Terminal Console**: Pemantauan proses unduhan live non-blocking berbasis `QProcess` dengan fitur stop aman (membersihkan proses child `ffmpeg`/`yt-dlp`).

### 2. ⚙️ Tab Pengaturan (Settings & Persistent Storage)
- **Penyimpanan Pengaturan Otomatis (`config.json`)**:
  - Lokasi folder unduhan, pilihan runner, custom syntax, extra flags, cookie file, dan format audio **tersimpan secara otomatis**.
  - Saat aplikasi dibuka kembali, semua preferensi Anda langsung aktif tanpa perlu disetel ulang.
- **Pilihan Runner Fleksibel**:
  - `Langsung dari EXE` (`.\spotdl.exe`)
  - `Python (python -m spotdl)`
  - `Python (py -m spotdl)`
  - `Custom Syntax` (misalnya `python spotdl`, `py -m spotdl`, path custom)
- **Kotak Custom Syntax & Extra Flags**:
  - Sesuaikan command base dan tambahkan flag sesuka hati (misal: `--bitrate 320k --threads 4`).
- **Folder Output**: Default `./Song` dengan tombol ganti folder dan *↗ Buka Folder di Explorer*.
- **Cookie File YouTube**: Toggle dan browse file `cookies.txt`.
- **Format Audio**: Pilihan cepat `mp3`, `m4a`, `flac`, `opus`, `ogg`, `wav`.
- **Live Command Template Preview**: Menampilkan template perintah CLI secara real-time.

## 📦 Instalasi di Komputer Baru (Windows)

Prasyarat: Windows 10/11 dengan **App Installer** agar perintah `winget` tersedia.

1. Clone atau ekstrak proyek, lalu buka PowerShell pada folder proyek.
2. Jalankan skrip persiapan satu kali:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

Skrip ini memasang `uv`, FFmpeg, dan Deno melalui `winget`, lalu menjalankan `uv sync` untuk membuat environment Python dan memasang dependensi yang dikunci di `uv.lock`.

FFmpeg diperlukan untuk konversi audio. Deno diperlukan oleh yt-dlp pada sebagian unduhan YouTube.

## 🚀 Cara Menjalankan

Anda dapat menjalankan aplikasi dengan salah satu cara berikut:

1. **Klik Dua Kali**:
   - Jalankan file `run_ui.bat` setelah proses persiapan selesai.
2. **Melalui Terminal**:
   ```powershell
   uv run app.py
   ```

