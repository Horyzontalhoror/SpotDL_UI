from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QTableWidgetItem

import os
import subprocess
import platform
import time
import re
from pathlib import Path

class LinkManagerMixin:
    """Mixin untuk manajemen link, input multi-baris, dan manipulasi baris tabel antrean."""

    def paste_to_multi_input(self):
        text = QApplication.clipboard().text()
        if text:
            self.txt_multi_links.insertPlainText(text)

    def detect_link_type(self, link_str: str) -> str:
        if "|" in link_str:
            return "YT + Spotify Metadata"
        elif "spotify.com" in link_str.lower():
            return "Spotify"
        elif "youtube.com" in link_str.lower() or "youtu.be" in link_str.lower():
            return "YouTube"
        else:
            return "Query / Audio"

    def add_links_to_queue(self):
        raw_text = self.txt_multi_links.toPlainText()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            QMessageBox.warning(self, "Input Kosong", "Silakan masukkan setidaknya satu link pada kotak input.")
            return

        added_count = 0
        for line in lines:
            link_type = self.detect_link_type(line)
            row = self.tbl_queue.rowCount()
            self.tbl_queue.insertRow(row)

            item_no = QTableWidgetItem(str(row + 1))
            item_no.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_type = QTableWidgetItem(link_type)
            item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Judul lagu awalnya kosong; akan diperbarui setelah download selesai
            item_title = QTableWidgetItem("—")
            item_title.setForeground(QColor("#8b949e"))
            item_link = QTableWidgetItem(line)
            item_status = QTableWidgetItem("⏳ Menunggu")
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setForeground(QColor("#c9d1d9"))
            # Path file hasil download (disembunyikan)
            item_path = QTableWidgetItem("")

            self.tbl_queue.setItem(row, 0, item_no)
            self.tbl_queue.setItem(row, 1, item_type)
            self.tbl_queue.setItem(row, 2, item_title)  # Judul Lagu (kol. 2)
            self.tbl_queue.setItem(row, 3, item_link)   # Link (kol. 3)
            self.tbl_queue.setItem(row, 4, item_status) # Status (kol. 4)
            self.tbl_queue.setItem(row, 5, item_path)   # Path (kol. 5)
            added_count += 1

        self.txt_multi_links.clear()
        self.update_queue_count()
        self.append_log(f"➕ Ditambahkan {added_count} link ke daftar antrean.\n")

    def update_queue_count(self):
        total = self.tbl_queue.rowCount()
        pending = 0
        done = 0
        failed = 0
        for r in range(total):
            st = self.tbl_queue.item(r, 4).text()  # Status ada di kolom 4
            if "Selesai" in st:
                done += 1
            elif "Gagal" in st or "Batal" in st:
                failed += 1
            else:
                pending += 1
        self.lbl_queue_count.setText(f"Total: {total} | ⏳ Menunggu: {pending} | ✅ Selesai: {done} | ❌ Gagal: {failed}")

    def remove_selected_items(self):
        selected_rows = sorted(set(index.row() for index in self.tbl_queue.selectedIndexes()), reverse=True)
        if not selected_rows:
            return
        for r in selected_rows:
            # Cegah menghapus item yang sedang aktif mendownload
            if r == self.current_queue_row:
                continue
            self.tbl_queue.removeRow(r)
        self.reindex_queue()
        self.update_queue_count()

    def remove_finished_items(self):
        for r in range(self.tbl_queue.rowCount() - 1, -1, -1):
            st = self.tbl_queue.item(r, 4).text()  # Status ada di kolom 4
            if "Selesai" in st and r != self.current_queue_row:
                self.tbl_queue.removeRow(r)
        self.reindex_queue()
        self.update_queue_count()

    def reset_failed_items(self):
        count = 0
        for r in range(self.tbl_queue.rowCount()):
            st = self.tbl_queue.item(r, 4).text()  # Status ada di kolom 4
            if "Gagal" in st or "Batal" in st:
                item = self.tbl_queue.item(r, 4)
                item.setText("⏳ Menunggu")
                item.setForeground(QColor("#c9d1d9"))
                count += 1
        self.update_queue_count()
        self.append_log(f"🔄 Berhasil mereset {count} item gagal kembali menjadi status 'Menunggu'.\n")

    def reset_selected_failed_items(self):
        """Mereset baris yang dipilih jika berstatus Gagal/Batal."""
        selected_rows = sorted(set(index.row() for index in self.tbl_queue.selectedIndexes()))
        targets = selected_rows if selected_rows else range(self.tbl_queue.rowCount())
        count = 0
        for r in targets:
            item = self.tbl_queue.item(r, 4)
            st = item.text() if item else ""
            if "Gagal" in st or "Batal" in st:
                item.setText("⏳ Menunggu")
                item.setForeground(QColor("#c9d1d9"))
                count += 1
        self.update_queue_count()
        if count > 0:
            self.append_log(f"🔄 Berhasil mereset {count} item terpilih kembali menjadi status 'Menunggu'.\n")

    def resolve_downloaded_file(self, row: int):
        """
        Mencari path file hasil unduhan untuk baris antrean tertentu.
        Mengecek file baru/termodifikasi, path yang tersimpan, atau mencocokkan judul lagu.
        """
        output_dir = self.txt_output_dir.text().strip() or getattr(self, "default_song_dir", "")
        if not output_dir or not os.path.exists(output_dir):
            return None

        audio_extensions = {".mp3", ".flac", ".m4a", ".opus", ".ogg", ".wav"}

        # 1. Cek file yang baru dibuat atau dimodifikasi selama download baris ini
        pre_files = getattr(self, "_pre_download_files", {})
        start_time = getattr(self, "_download_start_time", 0) - 3.0

        new_or_modified = []
        try:
            for root, _, files in os.walk(output_dir):
                for f in files:
                    p = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(p)
                        if p not in pre_files or mtime > pre_files[p]:
                            if mtime >= start_time:
                                new_or_modified.append((p, mtime))
                    except OSError:
                        pass
        except Exception:
            pass

        if new_or_modified:
            new_or_modified.sort(key=lambda x: x[1], reverse=True)
            for p, _ in new_or_modified:
                if Path(p).suffix.lower() in audio_extensions:
                    return str(Path(p).resolve())
            return str(Path(new_or_modified[0][0]).resolve())

        # 2. Cek path yang sudah tersimpan di kolom 5
        item_path = self.tbl_queue.item(row, 5)
        if item_path and item_path.text().strip():
            existing_path = item_path.text().strip()
            if os.path.exists(existing_path):
                return str(Path(existing_path).resolve())

        # 3. Fallback: Cari file yang namanya cocok dengan judul lagu (kolom 2)
        title_item = self.tbl_queue.item(row, 2)
        title = title_item.text().strip() if title_item else ""
        if title and title not in ("—", "", "..."):
            clean_title = re.sub(r'[\\/*?:"<>|]', '', title).lower().strip()
            try:
                for root, _, files in os.walk(output_dir):
                    for f in files:
                        p = os.path.join(root, f)
                        stem = Path(p).stem.lower().strip()
                        if Path(p).suffix.lower() in audio_extensions:
                            if clean_title == stem or clean_title in stem or stem in clean_title:
                                return str(Path(p).resolve())
            except Exception:
                pass

        return None

    # lokasi file hasil download ke tabel
    def set_download_file_path(self, row, file_path_or_name):
        """
        Simpan lokasi file hasil download ke tabel (kolom 5).
        Dipanggil setelah download selesai.
        """
        if not file_path_or_name or row >= self.tbl_queue.rowCount():
            return

        p = Path(file_path_or_name)
        if not p.is_absolute():
            output_dir = self.txt_output_dir.text().strip() or getattr(self, "default_song_dir", "")
            p = Path(output_dir) / p

        full_path = str(p.resolve())
        item = self.tbl_queue.item(row, 5)
        if not item:
            item = QTableWidgetItem(full_path)
            self.tbl_queue.setItem(row, 5, item)
        else:
            item.setText(full_path)

    # --- Membuka lokasi file hasil download ---
    def open_file_location(self):
        selected_rows = list(set(
            index.row()
            for index in self.tbl_queue.selectedIndexes()
        ))
        if len(selected_rows) != 1:
            return
        row = selected_rows[0]

        # Validasi status baris
        status_item = self.tbl_queue.item(row, 4)
        status_text = status_item.text() if status_item else ""
        if "Mengunduh" in status_text:
            QMessageBox.information(self, "Lokasi File", "Download sedang berlangsung.")
            return
        if "Gagal" in status_text or "Batal" in status_text:
            QMessageBox.warning(self, "Lokasi File", "File tidak tersedia karena unduhan gagal atau dibatalkan.")
            return

        file_path_str = ""
        item = self.tbl_queue.item(row, 5)
        if item and item.text().strip():
            file_path_str = item.text().strip()

        # Coba resolve jika belum tersimpan atau file dipindahkan
        if not file_path_str or not os.path.exists(file_path_str):
            resolved = self.resolve_downloaded_file(row)
            if resolved and os.path.exists(resolved):
                file_path_str = resolved
                self.set_download_file_path(row, resolved)

        if not file_path_str or not os.path.exists(file_path_str):
            QMessageBox.warning(
                self,
                "File Tidak Ditemukan",
                "File hasil unduhan belum tersedia atau tidak ditemukan di disk."
            )
            return

        file_path = Path(file_path_str).resolve()
        self.append_log(f"📂 Membuka lokasi file: {file_path}\n")

        try:
            if platform.system() == "Windows":
                norm_path = os.path.normpath(str(file_path))
                if os.path.isfile(norm_path):
                    subprocess.Popen(f'explorer /select,"{norm_path}"')
                else:
                    os.startfile(norm_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", str(file_path)])
            else:
                folder = str(file_path.parent if file_path.is_file() else file_path)
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            QMessageBox.warning(self, "Gagal Membuka File", f"Tidak dapat membuka file/folder: {e}")

    def reindex_queue(self):
        for r in range(self.tbl_queue.rowCount()):
            self.tbl_queue.item(r, 0).setText(str(r + 1))

    # =========================================================================
    # CONTEXT MENU TABEL ANTREAN
    # =========================================================================
    def show_queue_context_menu(self, pos):
        """Menampilkan context menu klik kanan pada tabel antrean."""
        row_at_pos = self.tbl_queue.rowAt(pos.y())
        selected_rows = list(set(index.row() for index in self.tbl_queue.selectedIndexes()))
        if row_at_pos >= 0 and row_at_pos not in selected_rows:
            self.tbl_queue.selectRow(row_at_pos)
            selected_rows = [row_at_pos]

        if not selected_rows:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 7px 22px 7px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1f3a5f;
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #555555;
            }
            QMenu::separator {
                height: 1px;
                background: #30363d;
                margin: 4px 6px;
            }
        """)

        # Cek apakah proses antrean/download sedang aktif berjalan
        is_process_running = (
            hasattr(self, "process")
            and self.process is not None
            and self.process.state() == QProcess.ProcessState.Running
        )
        current_active_row = getattr(self, "current_queue_row", None)
        is_queue_running = is_process_running or (current_active_row is not None)

        # Cek status baris yang sedang dipilih
        selected_statuses = [
            self.tbl_queue.item(r, 4).text() if self.tbl_queue.item(r, 4) else ""
            for r in selected_rows
        ]
        any_downloading = any(
            ("Mengunduh" in st) or (r == current_active_row)
            for r, st in zip(selected_rows, selected_statuses)
        )
        any_failed = any(
            ("Gagal" in st) or ("Batal" in st)
            for st in selected_statuses
        )
        has_downloadable = any(
            ("Selesai" not in st) and ("Mengunduh" not in st)
            for st in selected_statuses
        )

        # 1. Aksi: Download Terpilih
        # Disabled jika sedang mendownload (is_queue_running / any_downloading) atau tidak ada item untuk diunduh
        act_download = QAction("🎯 Download", self)
        can_download = (not is_queue_running) and (not any_downloading) and has_downloadable
        act_download.setEnabled(can_download)
        act_download.triggered.connect(self.start_download_selected)
        menu.addAction(act_download)

        menu.addSeparator()

        # 2. Aksi: Hapus Terpilih
        # Disabled jika sedang mendownload (is_queue_running / any_downloading)
        act_delete = QAction("🗑 Hapus", self)
        can_delete = (not is_queue_running) and (not any_downloading)
        act_delete.setEnabled(can_delete)
        act_delete.triggered.connect(self.remove_selected_items)
        menu.addAction(act_delete)

        # 3. Aksi: Reset Gagal
        act_reset = QAction("🔄 Reset Gagal", self)
        act_reset.setEnabled(any_failed and not is_queue_running)
        act_reset.triggered.connect(self.reset_selected_failed_items)
        menu.addAction(act_reset)

        menu.addSeparator()

        # 4. Aksi: Salin Link
        act_copy_link = QAction("📋 Salin Link", self)
        act_copy_link.setEnabled(len(selected_rows) == 1)
        def _copy_link():
            r = selected_rows[0]
            link = self.tbl_queue.item(r, 3).text()
            QApplication.clipboard().setText(link)
            self.append_log(f"📋 [Sistem] Link baris #{r + 1} disalin ke clipboard.\n")
        act_copy_link.triggered.connect(_copy_link)
        menu.addAction(act_copy_link)

        menu.addSeparator()

        # 5. Aksi: Buka Lokasi File
        # Disabled jika:
        # - Lebih dari 1 baris terpilih
        # - Status download sedang berlangsung (is_row_downloading / any_downloading)
        # - Status gagal (is_row_failed)
        # - Status bukan "Selesai" (misal: "Menunggu")
        # - File fisik tidak ditemukan di disk
        act_open_folder = QAction("📂 Buka Lokasi File", self)
        can_open_location = False
        if len(selected_rows) == 1:
            r = selected_rows[0]
            st = selected_statuses[0]
            is_row_downloading = ("Mengunduh" in st) or (r == current_active_row)
            is_row_failed = ("Gagal" in st) or ("Batal" in st)
            is_row_done = "Selesai" in st

            if not is_row_downloading and not is_row_failed and is_row_done:
                path_item = self.tbl_queue.item(r, 5)
                path_str = path_item.text().strip() if path_item else ""
                if path_str and os.path.exists(path_str):
                    can_open_location = True
                elif self.resolve_downloaded_file(r):
                    can_open_location = True

        act_open_folder.setEnabled(can_open_location)
        act_open_folder.triggered.connect(self.open_file_location)
        menu.addAction(act_open_folder)

        menu.exec(self.tbl_queue.viewport().mapToGlobal(pos))
