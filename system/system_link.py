from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem


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

            self.tbl_queue.setItem(row, 0, item_no)
            self.tbl_queue.setItem(row, 1, item_type)
            self.tbl_queue.setItem(row, 2, item_title)  # Judul Lagu (kol. 2)
            self.tbl_queue.setItem(row, 3, item_link)   # Link (kol. 3)
            self.tbl_queue.setItem(row, 4, item_status) # Status (kol. 4)
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

    def reindex_queue(self):
        for r in range(self.tbl_queue.rowCount()):
            self.tbl_queue.item(r, 0).setText(str(r + 1))
