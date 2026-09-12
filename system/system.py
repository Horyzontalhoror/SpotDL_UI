import os
import sys
import time
import subprocess
from pathlib import Path
from PyQt6.QtCore import QProcess
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox


class QueueEngineMixin:
    """Mixin untuk eksekusi proses antrean unduhan (download one-by-one via QProcess)."""

    def start_download_all_queue(self):
        """Mulai mendownload seluruh antrean yang berstatus 'Menunggu' atau 'Gagal' (Abaikan yang sudah selesai)."""
        target_indices = []
        for r in range(self.tbl_queue.rowCount()):
            st = self.tbl_queue.item(r, 4).text()  # Status ada di kolom 4
            # ABAIKAN YANG SUDAH SELESAI
            if "Selesai" not in st:
                target_indices.append(r)

        if not target_indices:
            QMessageBox.information(self, "Antrean Selesai", "Semua item dalam antrean sudah berstatus 'Selesai'!")
            return

        self.queue_indices = target_indices
        self.is_stopped_manually = False
        self.start_next_in_queue()

    def start_download_selected(self):
        """Hanya mendownload baris yang di-select pengguna yang belum berstatus 'Selesai'."""
        selected_rows = sorted(set(index.row() for index in self.tbl_queue.selectedIndexes()))
        if not selected_rows:
            QMessageBox.warning(self, "Pilih Item", "Silakan klik/pilih baris antrean yang ingin diunduh terlebih dahulu.")
            return

        target_indices = []
        for r in selected_rows:
            st = self.tbl_queue.item(r, 4).text()  # Status ada di kolom 4
            if "Selesai" not in st:
                target_indices.append(r)

        if not target_indices:
            QMessageBox.information(self, "Item Selesai", "Semua item terpilih sudah berstatus 'Selesai'!")
            return

        self.queue_indices = target_indices
        self.is_stopped_manually = False
        self.start_next_in_queue()

    def start_next_in_queue(self):
        if self.is_stopped_manually or not self.queue_indices:
            self.on_queue_completed()
            return

        self.current_queue_row = self.queue_indices.pop(0)
        row = self.current_queue_row

        # Update status baris tabel menjadi Mengunduh...
        status_item = self.tbl_queue.item(row, 4)  # Status ada di kolom 4
        status_item.setText("🔄 Mengunduh...")
        status_item.setForeground(QColor("#d29922"))
        self.tbl_queue.scrollToItem(status_item)

        target_query = self.tbl_queue.item(row, 3).text().strip()  # Link ada di kolom 3
        program, args, display_string = self.build_command_for_query(target_query)

        self.btn_download_all.setEnabled(False)
        self.btn_download_selected.setEnabled(False)
        self.btn_stop.setEnabled(True)

        remaining = len(self.queue_indices) + 1
        self.status_badge.setText(f"● Mengunduh #{row + 1} (Sisa: {remaining})")
        self.status_badge.setStyleSheet("""
            background-color: #22272e;
            color: #d29922;
            font-weight: bold;
            padding: 6px 14px;
            border-radius: 12px;
            border: 1px solid #bb8009;
        """)

        self.append_log(f"\n▶ [Antrean #{row + 1}] Memulai download: {target_query}\n")
        self.append_log(f"   Command: {display_string}\n")
        self.append_log("-" * 65 + "\n")

        # Catat daftar file sebelum download untuk mendeteksi file hasil download
        out_dir = self.txt_output_dir.text().strip() or getattr(self, "default_song_dir", "")
        self._download_start_time = time.time()
        self._pre_download_files = {}
        if out_dir and os.path.exists(out_dir):
            try:
                for root, _, files in os.walk(out_dir):
                    for f in files:
                        p = os.path.join(root, f)
                        try:
                            self._pre_download_files[p] = os.path.getmtime(p)
                        except OSError:
                            pass
            except Exception:
                pass

        self.process = QProcess(self)
        self.process.setWorkingDirectory(self.current_dir)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_process_finished)

        self.process.start(program, args)
        if not self.process.waitForStarted(3000):
            self.append_log(f"❌ Gagal menjalankan proses '{program}'. Pastikan perintah tersedia di PATH.\n")
            self.on_process_finished(-1, QProcess.ExitStatus.CrashExit)

    def on_process_finished(self, exit_code, exit_status):
        row = self.current_queue_row
        if row is not None and row < self.tbl_queue.rowCount():
            status_item = self.tbl_queue.item(row, 4)  # Status ada di kolom 4
            if self.is_stopped_manually:
                status_item.setText("⏹ Dibatalkan")
                status_item.setForeground(QColor("#f85149"))
                path_item = self.tbl_queue.item(row, 5)
                if path_item:
                    path_item.setText("")
            elif exit_code == 0:
                status_item.setText("✅ Selesai")
                status_item.setForeground(QColor("#57ab5a"))

                # Cari dan simpan lokasi file yang baru selesai diunduh
                downloaded_file = self.resolve_downloaded_file(row)
                if downloaded_file:
                    self.set_download_file_path(row, downloaded_file)
                    title_item = self.tbl_queue.item(row, 2)
                    if title_item and title_item.text() in ("—", "", "..."):
                        title_item.setText(Path(downloaded_file).stem)

                # Finalisasi warna kolom Judul Lagu menjadi hijau (berhasil)
                title_item = self.tbl_queue.item(row, 2)
                if title_item and title_item.text() not in ("—", "", "..."):
                    title_item.setForeground(QColor("#57ab5a"))
                self.append_log(f"✨ [Antrean #{row + 1}] Berhasil diselesaikan!\n\n")
            else:
                status_item.setText("❌ Gagal")
                status_item.setForeground(QColor("#f85149"))
                path_item = self.tbl_queue.item(row, 5)
                if path_item:
                    path_item.setText("")
                self.append_log(f"⚠️ [Antrean #{row + 1}] Gagal diunduh (Kode: {exit_code}).\n\n")

        self.current_queue_row = None
        self.update_queue_count()

        # Lanjutkan ke item antrean berikutnya
        if not self.is_stopped_manually and self.queue_indices:
            self.start_next_in_queue()
        else:
            self.on_queue_completed()

    def stop_queue_download(self):
        self.is_stopped_manually = True
        self.queue_indices.clear()
        self.append_log("\n⚠️ [Sistem] Menghentikan antrean unduhan...\n")

        if self.process and self.process.state() == QProcess.ProcessState.Running:
            pid = self.process.processId()
            self.process.terminate()
            if not self.process.waitForFinished(1500):
                if sys.platform == "win32" and pid > 0:
                    try:
                        subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
                    except Exception:
                        pass
                self.process.kill()

        self.on_queue_completed()

    def on_queue_completed(self):
        self.btn_download_all.setEnabled(True)
        self.btn_download_selected.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.current_queue_row = None

        if self.is_stopped_manually:
            self.status_badge.setText("● Berhenti")
            self.status_badge.setStyleSheet("""
                background-color: #22272e;
                color: #f85149;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 12px;
                border: 1px solid #da3633;
            """)
        else:
            self.status_badge.setText("● Selesai")
            self.status_badge.setStyleSheet("""
                background-color: #22272e;
                color: #57ab5a;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 12px;
                border: 1px solid #347d39;
            """)
