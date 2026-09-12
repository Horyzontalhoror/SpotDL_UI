from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QTextEdit,
    QPushButton, QLabel, QTableWidget, QHeaderView,
    QAbstractItemView, QCheckBox
)


class DownloadTabMixin:
    """Mixin untuk membangun dan mengelola UI Tab 1 (Download & Antrean)."""

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

        self.tbl_queue = QTableWidget(0, 6)
        self.tbl_queue.setHorizontalHeaderLabels(["#", "Tipe", "Judul Lagu", "Link / Target Query", "Status", "File Path"])
        self.tbl_queue.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.setColumnHidden(5, True)
        self.tbl_queue.setColumnWidth(2, 200)
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

        # Aktifkan context menu klik kanan pada tabel antrean
        self.tbl_queue.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl_queue.customContextMenuRequested.connect(self.show_queue_context_menu)

        # Kontrol Antrean (Download All, Download Selected, Stop, Reset, Delete)
        queue_ctrl_layout = QHBoxLayout()
        queue_ctrl_layout.setSpacing(8)

        self.btn_download_all = QPushButton("▶️ Download")
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

        self.btn_stop = QPushButton("⏹ Batalkan")
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

        btn_retry_failed = QPushButton("🔄 Reset Gagal")
        btn_retry_failed.setToolTip("Kembalikan item berstatus Gagal menjadi Menunggu agar dapat diunduh ulang")
        btn_retry_failed.clicked.connect(self.reset_failed_items)

        btn_remove_selected = QPushButton("🗑 Hapus Terpilih")
        btn_remove_selected.clicked.connect(self.remove_selected_items)

        btn_remove_done = QPushButton("🧹 Hapus Selesai")
        btn_remove_done.clicked.connect(self.remove_finished_items)

        queue_ctrl_layout.addWidget(self.btn_download_all)
        # queue_ctrl_layout.addWidget(self.btn_download_selected)
        queue_ctrl_layout.addWidget(self.btn_stop)
        queue_ctrl_layout.addWidget(btn_retry_failed)
        # queue_ctrl_layout.addWidget(btn_remove_selected)
        queue_ctrl_layout.addWidget(btn_remove_done)
        queue_ctrl_layout.addStretch()

        queue_layout.addLayout(queue_ctrl_layout)
        tab_layout.addWidget(queue_group, 1)

        # Bagian 3: Live Terminal Log
        log_group = QGroupBox("💻 Terminal Log")
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
