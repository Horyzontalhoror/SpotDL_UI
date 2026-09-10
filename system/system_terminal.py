import os
import re
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import QFileDialog, QMessageBox

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# Pola regex untuk menangkap judul lagu dari output SpotDL
# SpotDL biasanya mencetak:
#   Downloading "Mazzy Star - Fade Into You"
#   Downloaded "Mazzy Star - Fade Into You"
#   Fetching metadata for Mazzy Star - Fade Into You
#   Found song: Artist - Title
_TITLE_PATTERNS = [
    # "Downloading "Artist - Title"" atau "Downloaded "Artist - Title""
    re.compile(r'(?:Downloading|Downloaded)\s+"([^"]+)"', re.IGNORECASE),
    # "Downloading Artist - Title" (tanpa tanda kutip)
    re.compile(r'Downloading\s+(.+?)\s*\.{3}', re.IGNORECASE),
    # "Found song: Artist - Title"
    re.compile(r'Found\s+song\s*:\s*(.+)', re.IGNORECASE),
    # "Fetching metadata for Artist - Title"
    re.compile(r'Fetching\s+(?:metadata\s+for\s+)?(.+)', re.IGNORECASE),
    # "Song: Artist - Title"
    re.compile(r'^Song\s*:\s*(.+)', re.IGNORECASE),
]


class TerminalLoggerMixin:
    """Mixin untuk logging terminal real-time, filter escape ANSI, dan helper dialog file/folder."""

    def browse_output_dir(self):
        current = self.txt_output_dir.text().strip() or self.current_dir
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Output Unduhan", current)
        if folder:
            self.txt_output_dir.setText(folder)
            self.save_settings()

    def open_output_dir(self):
        folder = self.txt_output_dir.text().strip() or self.default_song_dir
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        try:
            os.startfile(folder)
        except Exception as e:
            QMessageBox.warning(self, "Gagal Membuka Folder", f"Tidak dapat membuka folder: {e}")

    def browse_cookie_file(self):
        initial = self.current_dir
        path, _ = QFileDialog.getOpenFileName(self, "Pilih File Cookies", initial, "Text Files (*.txt);;All Files (*)")
        if path:
            self.txt_cookie_path.setText(path)
            self.chk_cookie.setChecked(True)
            self.save_settings()

    def append_log(self, text: str):
        cursor = self.txt_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        if self.chk_autoscroll.isChecked():
            self.txt_log.setTextCursor(cursor)
            self.txt_log.ensureCursorVisible()

    def _try_extract_title(self, line: str):
        """
        Coba ekstrak judul lagu dari satu baris output SpotDL.
        Jika ditemukan dan baris antrean aktif ada, perbarui kolom Judul Lagu (kolom 2).
        """
        row = getattr(self, "current_queue_row", None)
        if row is None:
            return

        # Jangan overwrite jika sudah diisi judul nyata (bukan "—")
        title_item = self.tbl_queue.item(row, 2)
        if title_item and title_item.text() not in ("—", "", "..."):
            return

        for pattern in _TITLE_PATTERNS:
            match = pattern.search(line)
            if match:
                candidate = match.group(1).strip()
                # Filter: minimal mengandung spasi atau tanda "-" (kemungkinan "Artist - Title")
                # dan panjang wajar (5–100 karakter)
                if 5 <= len(candidate) <= 100:
                    if title_item:
                        title_item.setText(candidate)
                        title_item.setForeground(QColor("#d29922"))  # kuning = sedang diunduh
                    return

    def handle_terminal_output(self, raw_data: bytes):
        text = raw_data.decode("utf-8", errors="replace")
        clean_text = ANSI_ESCAPE_RE.sub('', text)

        lines = clean_text.split('\r')
        for i, chunk in enumerate(lines):
            if i > 0:
                cursor = self.txt_log.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
            self.append_log(chunk)

            # Coba ekstrak judul lagu dari setiap baris output
            self._try_extract_title(chunk)

    def on_stdout(self):
        if self.process:
            data = self.process.readAllStandardOutput().data()
            self.handle_terminal_output(data)

    def on_stderr(self):
        if self.process:
            data = self.process.readAllStandardError().data()
            self.handle_terminal_output(data)
