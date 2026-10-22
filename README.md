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

## 📦 Instalasi & Virtual Environment (venv)

Virtual environment (`venv`) telah dibuat dan disiapkan di direktori ini.

### Daftar Paket Pip yang Dibutuhkan
1. **`PyQt6>=6.5.0`** : Framework antarmuka GUI desktop native.
2. **`pyqtdarktheme>=2.1.0`** : Tema modern dark mode dengan kustomisasi warna aksen Spotify.
3. **`spotdl>=4.3.0`** : Core SpotDL downloader (beserta dependensinya: `yt-dlp`, `spotipy`, `mutagen`, `pydub`, dll) jika menggunakan runner Python.

### Perintah Instalasi Manual (jika diperlukan di komputer/lingkungan lain):
```powershell
# 1. Buat virtual environment
python -m venv venv

# 2. Aktivasi venv
# PowerShell:
.\venv\Scripts\Activate.ps1
# Atau CMD:
venv\Scripts\activate.bat

# 3. Install paket yang dibutuhkan
pip install -r requirements.txt
```

## 🚀 Cara Menjalankan

Anda dapat menjalankan aplikasi dengan salah satu cara berikut:

1. **Klik Dua Kali**:
   - Jalankan file `run_ui.bat` (otomatis mendeteksi dan menggunakan `venv`).
2. **Melalui Terminal dengan venv**:
   ```powershell
   .\venv\Scripts\python.exe app.py
   ```

