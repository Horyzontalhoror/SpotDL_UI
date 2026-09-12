import os
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QButtonGroup,
    QRadioButton, QLabel, QLineEdit, QPushButton,
    QCheckBox, QComboBox, QMessageBox
)


class SettingTabMixin:
    """Mixin untuk membangun dan mengelola UI Tab 2 (Pengaturan / Settings)."""

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

        btn_save_now = QPushButton("💾 Simpan")
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
