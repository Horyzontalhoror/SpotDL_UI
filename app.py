import sys
import os
import re
import json
import shlex
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QCheckBox, QFileDialog, QTextEdit, QGroupBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QMessageBox, QSplitter, QAbstractItemView
)
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont, QColor, QTextCursor
import qdarktheme

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class SpotDLApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpotDL Modern GUI Downloader")
        self.resize(1020, 860)
        self.setMinimumSize(900, 720)

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.exe_path = os.path.join(self.current_dir, "spotdl.exe")
        self.default_song_dir = os.path.join(self.current_dir, "Song")
        self.config_path = os.path.join(self.current_dir, "config.json")
        
        # Pastikan direktori Song ada
        if not os.path.exists(self.default_song_dir):
            os.makedirs(self.default_song_dir, exist_ok=True)

        self.process = None
        self.queue_indices = []
        self.current_queue_row = None
        self.is_stopped_manually = False

        self.init_ui()
        self.load_settings()
        self.update_command_preview()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(16, 14, 16, 14)

        # ---------------- HEADER ----------------
        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)

        title_label = QLabel("🎵 SpotDL Downloader GUI")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1DB954;")
        
        subtitle_label = QLabel("Unduh musik Spotify & YouTube secara batch dengan antrean cerdas dan metadata lengkap")
        subtitle_label.setStyleSheet("font-size: 12px; color: #888888;")

        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()

        self.status_badge = QLabel("● Siap")
        self.status_badge.setStyleSheet("""
            background-color: #22272e;
            color: #57ab5a;
            font-weight: bold;
            padding: 6px 14px;
            border-radius: 12px;
            border: 1px solid #347d39;
        """)
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # ---------------- TAB WIDGET ----------------
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #30363d;
                border-radius: 8px;
                background-color: #161b22;
                top: -1px;
            }
            QTabBar::tab {
                background: #0d1117;
                color: #8b949e;
                padding: 8px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #161b22;
                color: #1DB954;
                border-bottom: 2px solid #1DB954;
            }
            QTabBar::tab:hover {
                color: #ffffff;
            }
        """)

        # Tab 1: Download & Antrean
        self.tab_queue = QWidget()
        self.init_tab_queue()
        self.tabs.addTab(self.tab_queue, "📥 Download & Antrean")

        # Tab 2: Pengaturan
        self.tab_settings = QWidget()
        self.init_tab_settings()
        self.tabs.addTab(self.tab_settings, "⚙️ Pengaturan")

        main_layout.addWidget(self.tabs, 1)

    # =========================================================================
    # TAB 1: DOWNLOAD & ANTREAN
    # =========================================================================
    def init_tab_queue(self):
        tab_layout = QVBoxLayout(self.tab_queue)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(12, 12, 12, 12)

        # Bagian 1: Input Multi-Link
        input_group = QGroupBox("📝 Input Link (Bisa Paste Banyak Link Sekaligus - 1 Link Per Baris)")
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(6)

        self.txt_multi_links = QTextEdit()
        self.txt_multi_links.setFixedHeight(75)
        self.txt_multi_links.setPlaceholderText(
            "Paste link di sini (1 per baris):\n"
            "• Link Spotify (Lagu, Playlist, Album): https://open.spotify.com/track/...\n"
            "• Link YouTube: https://www.youtube.com/watch?v=...\n"
            "• Kombinasi Audio YouTube + Metadata Spotify: https://youtube.com/...|https://open.spotify.com/..."
        )
        self.txt_multi_links.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: Consolas, monospace;
                font-size: 12px;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        input_layout.addWidget(self.txt_multi_links)

        # Tombol Aksi Input Link
        input_btn_layout = QHBoxLayout()
        btn_paste = QPushButton("📋 Paste dari Clipboard")
        btn_add = QPushButton("➕ Tambahkan ke Antrean")
        btn_add.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 6px 14px;")
        btn_clear_input = QPushButton("✖ Bersihkan Input")

        btn_paste.clicked.connect(self.paste_to_multi_input)
        btn_add.clicked.connect(self.add_links_to_queue)
        btn_clear_input.clicked.connect(lambda: self.txt_multi_links.clear())

        input_btn_layout.addWidget(btn_paste)
        input_btn_layout.addWidget(btn_add)
        input_btn_layout.addWidget(btn_clear_input)
        input_btn_layout.addStretch()

        self.lbl_queue_count = QLabel("Total Antrean: 0 Lagu")
        self.lbl_queue_count.setStyleSheet("font-weight: bold; color: #58a6ff;")
        input_btn_layout.addWidget(self.lbl_queue_count)

        input_layout.addLayout(input_btn_layout)
        tab_layout.addWidget(input_group)

        # Bagian 2: Tabel Antrean
        queue_group = QGroupBox("📋 Daftar Antrean Unduhan")
        queue_layout = QVBoxLayout(queue_group)
        queue_layout.setSpacing(6)

        self.tbl_queue = QTableWidget(0, 4)
        self.tbl_queue.setHorizontalHeaderLabels(["#", "Tipe", "Link / Target Query", "Status"])
        self.tbl_queue.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_queue.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tbl_queue.setStyleSheet("""
            QTableWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                gridline-color: #21262d;
            }
            QTableWidget::item:selected {
                background-color: #1f3a5f;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #161b22;
                color: #8b949e;
                padding: 5px;
                border: 1px solid #21262d;
                font-weight: bold;
            }
        """)
        queue_layout.addWidget(self.tbl_queue)

        # Kontrol Antrean (Download All, Download Selected, Stop, Reset, Delete)
        queue_ctrl_layout = QHBoxLayout()
        queue_ctrl_layout.setSpacing(8)

        self.btn_download_all = QPushButton("▶ Download Semua Antrean")
        self.btn_download_all.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: #000000;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1ed760; }
            QPushButton:disabled { background-color: #33553d; color: #888888; }
        """)
        self.btn_download_all.clicked.connect(self.start_download_all_queue)

        self.btn_download_selected = QPushButton("🎯 Download Item Terpilih")
        self.btn_download_selected.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb;
                color: white;
                font-weight: bold;
                padding: 8px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #388bfd; }
            QPushButton:disabled { background-color: #1b3a6b; color: #888888; }
        """)
        self.btn_download_selected.clicked.connect(self.start_download_selected)

        self.btn_stop = QPushButton("⏹ Batalkan / Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #da3633;
                color: white;
                font-weight: bold;
                padding: 8px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #f85149; }
            QPushButton:disabled { background-color: #442726; color: #777777; }
        """)
        self.btn_stop.clicked.connect(self.stop_queue_download)

        btn_retry_failed = QPushButton("🔄 Reset Status Gagal")
        btn_retry_failed.setToolTip("Kembalikan item berstatus Gagal menjadi Menunggu agar dapat diunduh ulang")
        btn_retry_failed.clicked.connect(self.reset_failed_items)

        btn_remove_selected = QPushButton("🗑 Hapus Terpilih")
        btn_remove_selected.clicked.connect(self.remove_selected_items)

        btn_remove_done = QPushButton("🧹 Hapus Selesai")
        btn_remove_done.clicked.connect(self.remove_finished_items)

        queue_ctrl_layout.addWidget(self.btn_download_all)
        queue_ctrl_layout.addWidget(self.btn_download_selected)
        queue_ctrl_layout.addWidget(self.btn_stop)
        queue_ctrl_layout.addWidget(btn_retry_failed)
        queue_ctrl_layout.addWidget(btn_remove_selected)
        queue_ctrl_layout.addWidget(btn_remove_done)
        queue_ctrl_layout.addStretch()

        queue_layout.addLayout(queue_ctrl_layout)
        tab_layout.addWidget(queue_group, 1)

        # Bagian 3: Live Terminal Log
        log_group = QGroupBox("💻 Live Terminal Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(4)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFixedHeight(160)
        self.txt_log.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: Consolas, "Segoe UI Mono", monospace;
                font-size: 11px;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        log_layout.addWidget(self.txt_log)

        log_bottom_layout = QHBoxLayout()
        btn_clear_log = QPushButton("🧹 Bersihkan Log")
        btn_clear_log.clicked.connect(lambda: self.txt_log.clear())

        self.chk_autoscroll = QCheckBox("Auto-Scroll Log")
        self.chk_autoscroll.setChecked(True)

        log_bottom_layout.addWidget(btn_clear_log)
        log_bottom_layout.addWidget(self.chk_autoscroll)
        log_bottom_layout.addStretch()
        log_layout.addLayout(log_bottom_layout)

        tab_layout.addWidget(log_group)

    # =========================================================================
    # TAB 2: PENGATURAN (SETTINGS)
    # =========================================================================
    def init_tab_settings(self):
        tab_layout = QVBoxLayout(self.tab_settings)
        tab_layout.setSpacing(12)
        tab_layout.setContentsMargins(14, 14, 14, 14)

        # 1. Runner & Sintaks
        runner_group = QGroupBox("⚙️ Metode Eksekusi & Sintaks SpotDL")
        runner_layout = QVBoxLayout(runner_group)
        runner_layout.setSpacing(8)

        radio_layout = QHBoxLayout()
        self.btn_group = QButtonGroup(self)

        self.radio_exe = QRadioButton("Langsung dari EXE (spotdl.exe)")
        self.radio_py_module = QRadioButton("Python (python -m spotdl)")
        self.radio_py_launcher = QRadioButton("Python (py -m spotdl)")
        self.radio_custom = QRadioButton("Custom Syntax")

        self.btn_group.addButton(self.radio_exe, 1)
        self.btn_group.addButton(self.radio_py_module, 2)
        self.btn_group.addButton(self.radio_py_launcher, 3)
        self.btn_group.addButton(self.radio_custom, 4)

        radio_layout.addWidget(self.radio_exe)
        radio_layout.addWidget(self.radio_py_module)
        radio_layout.addWidget(self.radio_py_launcher)
        radio_layout.addWidget(self.radio_custom)
        radio_layout.addStretch()
        runner_layout.addLayout(radio_layout)

        if not os.path.exists(self.exe_path):
            self.radio_exe.setEnabled(False)
            self.radio_exe.setText("Langsung dari EXE (Tidak ditemukan spotdl.exe)")
            self.radio_py_module.setChecked(True)
        else:
            self.radio_exe.setChecked(True)

        syntax_row = QHBoxLayout()
        syntax_row.setSpacing(10)

        col1 = QVBoxLayout()
        lbl1 = QLabel("Sintaks Awalan Perintah (Command Base / Custom Syntax):")
        lbl1.setStyleSheet("font-size: 11px; color: #8b949e;")
        self.txt_custom_syntax = QLineEdit()
        self.txt_custom_syntax.setPlaceholderText("Contoh: py -m spotdl atau python spotdl atau .\\spotdl.exe")
        col1.addWidget(lbl1)
        col1.addWidget(self.txt_custom_syntax)

        col2 = QVBoxLayout()
        lbl2 = QLabel("Argumen / Flag Tambahan (Opsional):")
        lbl2.setStyleSheet("font-size: 11px; color: #8b949e;")
        self.txt_extra_flags = QLineEdit()
        self.txt_extra_flags.setPlaceholderText("Contoh: --bitrate 320k --threads 4 --overwrite force")
        col2.addWidget(lbl2)
        col2.addWidget(self.txt_extra_flags)

        syntax_row.addLayout(col1, 2)
        syntax_row.addLayout(col2, 2)
        runner_layout.addLayout(syntax_row)
        tab_layout.addWidget(runner_group)

        # 2. Folder Output
        folder_group = QGroupBox("📁 Folder Output Unduhan")
        folder_layout = QHBoxLayout(folder_group)
        folder_layout.setSpacing(8)

        lbl_out = QLabel("Folder Unduhan:")
        lbl_out.setFixedWidth(110)
        lbl_out.setStyleSheet("font-weight: bold;")
        self.txt_output_dir = QLineEdit(self.default_song_dir)
        btn_browse_folder = QPushButton("📂 Cari...")
        btn_open_folder = QPushButton("↗ Buka Folder")
        btn_browse_folder.setFixedWidth(80)
        btn_open_folder.setFixedWidth(110)
        btn_browse_folder.clicked.connect(self.browse_output_dir)
        btn_open_folder.clicked.connect(self.open_output_dir)

        folder_layout.addWidget(lbl_out)
        folder_layout.addWidget(self.txt_output_dir)
        folder_layout.addWidget(btn_browse_folder)
        folder_layout.addWidget(btn_open_folder)
        tab_layout.addWidget(folder_group)

        # 3. Cookie & Format Audio
        cookie_group = QGroupBox("🍪 Cookie YouTube & Format Audio")
        cookie_layout = QHBoxLayout(cookie_group)
        cookie_layout.setSpacing(10)

        self.chk_cookie = QCheckBox("Gunakan Cookie File (--cookie-file):")
        self.chk_cookie.setStyleSheet("font-weight: bold;")
        self.txt_cookie_path = QLineEdit()
        self.txt_cookie_path.setPlaceholderText("Path ke cookies.txt")
        self.txt_cookie_path.setEnabled(False)

        local_cookie = os.path.join(self.current_dir, "cookies.txt")
        if os.path.exists(local_cookie):
            self.txt_cookie_path.setText(local_cookie)
            self.chk_cookie.setChecked(True)
            self.txt_cookie_path.setEnabled(True)

        btn_browse_cookie = QPushButton("📄 Browse...")
        btn_browse_cookie.setFixedWidth(80)
        btn_browse_cookie.clicked.connect(self.browse_cookie_file)
        self.chk_cookie.toggled.connect(lambda checked: self.txt_cookie_path.setEnabled(checked))

        lbl_fmt = QLabel("Format:")
        lbl_fmt.setStyleSheet("font-weight: bold; margin-left: 10px;")
        self.combo_format = QComboBox()
        self.combo_format.addItems(["mp3", "m4a", "flac", "opus", "ogg", "wav"])
        self.combo_format.setFixedWidth(75)

        cookie_layout.addWidget(self.chk_cookie)
        cookie_layout.addWidget(self.txt_cookie_path)
        cookie_layout.addWidget(btn_browse_cookie)
        cookie_layout.addWidget(lbl_fmt)
        cookie_layout.addWidget(self.combo_format)
        tab_layout.addWidget(cookie_group)

        # 4. Preview Perintah CLI
        preview_group = QGroupBox("🔍 Preview Template Perintah CLI")
        preview_layout = QHBoxLayout(preview_group)
        self.txt_preview = QLineEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet("""
            background-color: #0d1117;
            color: #7ee787;
            font-family: Consolas, monospace;
            font-size: 12px;
            padding: 6px;
            border: 1px solid #30363d;
            border-radius: 4px;
        """)
        btn_copy_cmd = QPushButton("📋 Copy Template")
        btn_copy_cmd.setFixedWidth(120)
        btn_copy_cmd.clicked.connect(self.copy_command_preview)
        preview_layout.addWidget(self.txt_preview)
        preview_layout.addWidget(btn_copy_cmd)
        tab_layout.addWidget(preview_group)

        # 5. Tombol Simpan Pengaturan
        save_group = QGroupBox("💾 Penyimpanan Pengaturan (Persistent)")
        save_layout = QHBoxLayout(save_group)

        self.lbl_save_status = QLabel("✅ Pengaturan otomatis tersimpan setiap ada perubahan.")
        self.lbl_save_status.setStyleSheet("color: #57ab5a; font-size: 12px;")

        btn_save_now = QPushButton("💾 Simpan Pengaturan Sekarang")
        btn_save_now.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; padding: 6px 14px;")
        btn_save_now.clicked.connect(lambda: (self.save_settings(), QMessageBox.information(self, "Tersimpan", "Pengaturan berhasil disimpan!")))

        btn_reset_default = QPushButton("🔄 Reset Default")
        btn_reset_default.clicked.connect(self.reset_to_defaults)

        save_layout.addWidget(self.lbl_save_status)
        save_layout.addStretch()
        save_layout.addWidget(btn_save_now)
        save_layout.addWidget(btn_reset_default)
        tab_layout.addWidget(save_group)

        tab_layout.addStretch()

        # Connect signals tab settings
        self.radio_exe.toggled.connect(self.on_runner_changed)
        self.radio_py_module.toggled.connect(self.on_runner_changed)
        self.radio_py_launcher.toggled.connect(self.on_runner_changed)
        self.radio_custom.toggled.connect(self.on_runner_changed)

        self.txt_custom_syntax.textEdited.connect(self.on_custom_syntax_edited)
        self.txt_custom_syntax.textChanged.connect(self.on_setting_changed)
        self.txt_extra_flags.textChanged.connect(self.on_setting_changed)
        self.txt_output_dir.textChanged.connect(self.on_setting_changed)
        self.txt_cookie_path.textChanged.connect(self.on_setting_changed)
        self.chk_cookie.toggled.connect(self.on_setting_changed)
        self.combo_format.currentTextChanged.connect(self.on_setting_changed)

    # =========================================================================
    # PERSISTENT SETTINGS (LOAD & SAVE CONFIG.JSON)
    # =========================================================================
    def on_setting_changed(self):
        self.update_command_preview()
        self.save_settings()

    def save_settings(self):
        """Menyimpan konfigurasi ke config.json agar tidak perlu diatur ulang setiap membuka app"""
        runner = "custom"
        if self.radio_exe.isChecked():
            runner = "exe"
        elif self.radio_py_module.isChecked():
            runner = "py_module"
        elif self.radio_py_launcher.isChecked():
            runner = "py_launcher"

        config = {
            "runner": runner,
            "custom_syntax": self.txt_custom_syntax.text(),
            "extra_flags": self.txt_extra_flags.text(),
            "output_dir": self.txt_output_dir.text(),
            "use_cookie": self.chk_cookie.isChecked(),
            "cookie_path": self.txt_cookie_path.text(),
            "audio_format": self.combo_format.currentText(),
            "autoscroll": self.chk_autoscroll.isChecked()
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Gagal menyimpan config: {e}")

    def load_settings(self):
        """Memuat konfigurasi dari config.json jika ada"""
        if not os.path.exists(self.config_path):
            self.on_runner_changed()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            runner = config.get("runner", "exe")
            if runner == "exe" and os.path.exists(self.exe_path):
                self.radio_exe.setChecked(True)
            elif runner == "py_module":
                self.radio_py_module.setChecked(True)
            elif runner == "py_launcher":
                self.radio_py_launcher.setChecked(True)
            else:
                self.radio_custom.setChecked(True)

            if "custom_syntax" in config and config["custom_syntax"]:
                self.txt_custom_syntax.setText(config["custom_syntax"])
            if "extra_flags" in config:
                self.txt_extra_flags.setText(config["extra_flags"])
            if "output_dir" in config and config["output_dir"]:
                self.txt_output_dir.setText(config["output_dir"])
            if "use_cookie" in config:
                self.chk_cookie.setChecked(config["use_cookie"])
            if "cookie_path" in config:
                self.txt_cookie_path.setText(config["cookie_path"])
            if "audio_format" in config:
                self.combo_format.setCurrentText(config["audio_format"])
            if "autoscroll" in config:
                self.chk_autoscroll.setChecked(config["autoscroll"])

        except Exception as e:
            print(f"Error memuat config.json: {e}")
            self.on_runner_changed()

    def reset_to_defaults(self):
        reply = QMessageBox.question(self, "Konfirmasi Reset", "Kembalikan seluruh pengaturan ke default?")
        if reply == QMessageBox.StandardButton.Yes:
            if os.path.exists(self.exe_path):
                self.radio_exe.setChecked(True)
            else:
                self.radio_py_module.setChecked(True)
            self.on_runner_changed()
            self.txt_extra_flags.clear()
            self.txt_output_dir.setText(self.default_song_dir)
            self.chk_cookie.setChecked(False)
            self.txt_cookie_path.clear()
            self.combo_format.setCurrentText("mp3")
            self.save_settings()

    def on_custom_syntax_edited(self, text):
        if not self.radio_custom.isChecked():
            self.radio_custom.setChecked(True)

    def on_runner_changed(self):
        if self.radio_exe.isChecked():
            self.txt_custom_syntax.setText(".\\spotdl.exe")
        elif self.radio_py_module.isChecked():
            self.txt_custom_syntax.setText("python -m spotdl")
        elif self.radio_py_launcher.isChecked():
            self.txt_custom_syntax.setText("py -m spotdl")
        elif self.radio_custom.isChecked():
            if not self.txt_custom_syntax.text():
                self.txt_custom_syntax.setText("python spotdl")
        self.on_setting_changed()

    # =========================================================================
    # QUEUE & LINK MANAGEMENT
    # =========================================================================
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
            item_link = QTableWidgetItem(line)
            item_status = QTableWidgetItem("⏳ Menunggu")
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setForeground(QColor("#c9d1d9"))

            self.tbl_queue.setItem(row, 0, item_no)
            self.tbl_queue.setItem(row, 1, item_type)
            self.tbl_queue.setItem(row, 2, item_link)
            self.tbl_queue.setItem(row, 3, item_status)
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
            st = self.tbl_queue.item(r, 3).text()
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
            st = self.tbl_queue.item(r, 3).text()
            if "Selesai" in st and r != self.current_queue_row:
                self.tbl_queue.removeRow(r)
        self.reindex_queue()
        self.update_queue_count()

    def reset_failed_items(self):
        count = 0
        for r in range(self.tbl_queue.rowCount()):
            st = self.tbl_queue.item(r, 3).text()
            if "Gagal" in st or "Batal" in st:
                item = self.tbl_queue.item(r, 3)
                item.setText("⏳ Menunggu")
                item.setForeground(QColor("#c9d1d9"))
                count += 1
        self.update_queue_count()
        self.append_log(f"🔄 Berhasil mereset {count} item gagal kembali menjadi status 'Menunggu'.\n")

    def reindex_queue(self):
        for r in range(self.tbl_queue.rowCount()):
            self.tbl_queue.item(r, 0).setText(str(r + 1))

    # =========================================================================
    # QUEUE EXECUTION ENGINE (DOWNLOAD ONE BY ONE)
    # =========================================================================
    def start_download_all_queue(self):
        """Mulai mendownload seluruh antrean yang berstatus 'Menunggu' atau 'Gagal' (Abaikan yang sudah selesai)"""
        target_indices = []
        for r in range(self.tbl_queue.rowCount()):
            st = self.tbl_queue.item(r, 3).text()
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
        """Hanya mendownload baris yang di-select pengguna yang belum berstatus 'Selesai'"""
        selected_rows = sorted(set(index.row() for index in self.tbl_queue.selectedIndexes()))
        if not selected_rows:
            QMessageBox.warning(self, "Pilih Item", "Silakan klik/pilih baris antrean yang ingin diunduh terlebih dahulu.")
            return

        target_indices = []
        for r in selected_rows:
            st = self.tbl_queue.item(r, 3).text()
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
        status_item = self.tbl_queue.item(row, 3)
        status_item.setText("🔄 Mengunduh...")
        status_item.setForeground(QColor("#d29922"))
        self.tbl_queue.scrollToItem(status_item)

        target_query = self.tbl_queue.item(row, 2).text().strip()
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
            status_item = self.tbl_queue.item(row, 3)
            if self.is_stopped_manually:
                status_item.setText("⏹ Dibatalkan")
                status_item.setForeground(QColor("#f85149"))
            elif exit_code == 0:
                status_item.setText("✅ Selesai")
                status_item.setForeground(QColor("#57ab5a"))
                self.append_log(f"✨ [Antrean #{row + 1}] Berhasil diselesaikan!\n\n")
            else:
                status_item.setText("❌ Gagal")
                status_item.setForeground(QColor("#f85149"))
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

    # =========================================================================
    # COMMAND BUILDER
    # =========================================================================
    def build_command_for_query(self, target_query: str):
        base_cmd_str = self.txt_custom_syntax.text().strip() or "spotdl"

        try:
            cmd_parts = shlex.split(base_cmd_str, posix=False)
        except Exception:
            cmd_parts = base_cmd_str.split()

        if not cmd_parts:
            cmd_parts = ["spotdl"]

        program = cmd_parts[0]
        args = cmd_parts[1:]

        if target_query:
            args.append(target_query)

        out_dir = self.txt_output_dir.text().strip()
        if out_dir:
            args.extend(["--output", out_dir])

        if self.chk_cookie.isChecked():
            cookie_path = self.txt_cookie_path.text().strip()
            if cookie_path:
                args.extend(["--cookie-file", cookie_path])

        audio_fmt = self.combo_format.currentText()
        if audio_fmt:
            args.extend(["--format", audio_fmt])

        args.append("--simple-tui")

        extra_flags_str = self.txt_extra_flags.text().strip()
        if extra_flags_str:
            try:
                extra_args = shlex.split(extra_flags_str, posix=False)
                args.extend(extra_args)
            except Exception:
                args.extend(extra_flags_str.split())

        display_parts = []
        for p in [program] + args:
            if " " in p or "|" in p:
                display_parts.append(f'"{p}"')
            else:
                display_parts.append(p)
        display_string = " ".join(display_parts)

        return program, args, display_string

    def update_command_preview(self):
        try:
            _, _, display_string = self.build_command_for_query("<URL_LAGU>")
            self.txt_preview.setText(display_string)
        except Exception as e:
            self.txt_preview.setText(f"Error: {e}")

    def copy_command_preview(self):
        cmd = self.txt_preview.text()
        if cmd:
            QApplication.clipboard().setText(cmd)
            self.append_log("📋 [Sistem] Template perintah berhasil disalin ke clipboard!\n")

    # =========================================================================
    # TERMINAL LOGGING & HELPERS
    # =========================================================================
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

    def on_stdout(self):
        if self.process:
            data = self.process.readAllStandardOutput().data()
            self.handle_terminal_output(data)

    def on_stderr(self):
        if self.process:
            data = self.process.readAllStandardError().data()
            self.handle_terminal_output(data)


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    
    # Theme dark modern dengan aksen Spotify
    qdarktheme.setup_theme(
        theme="dark",
        custom_colors={
            "primary": "#1DB954"
        }
    )

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = SpotDLApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
