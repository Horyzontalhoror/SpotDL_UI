import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget
)
from PyQt6.QtGui import QFont
import qdarktheme

from UI.download import DownloadTabMixin
from UI.setting import SettingTabMixin
from system.system import QueueEngineMixin
from system.system_builder import CommandBuilderMixin
from system.system_link import LinkManagerMixin
from system.system_settings import SettingsManagerMixin
from system.system_terminal import TerminalLoggerMixin


class SpotDLApp(
    QMainWindow,
    DownloadTabMixin,
    SettingTabMixin,
    QueueEngineMixin,
    CommandBuilderMixin,
    LinkManagerMixin,
    SettingsManagerMixin,
    TerminalLoggerMixin
):
    """Aplikasi GUI SpotDL modern dengan arsitektur modular."""

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

        title_label = QLabel("SpotDL GUI")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1DB954;")

        subtitle_label = QLabel('Create by <a href="https://github.com/Horyzontalhoror/SpotDL_UI" style="color:#58a6ff; text-decoration:none;">Horyzontalhoror</a>')
        subtitle_label.setOpenExternalLinks(True)
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
        self.tabs.addTab(self.tab_queue, "📥 Download")

        # Tab 2: Pengaturan
        self.tab_settings = QWidget()
        self.init_tab_settings()
        self.tabs.addTab(self.tab_settings, "⚙️ Pengaturan")

        main_layout.addWidget(self.tabs, 1)


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)

    # Versi lama pyqtdarktheme hanya menyediakan load_stylesheet().
    # Gunakan setup_theme bila tersedia agar warna aksen dapat diterapkan.
    if hasattr(qdarktheme, "setup_theme"):
        qdarktheme.setup_theme(
            theme="dark",
            custom_colors={"primary": "#1DB954"},
        )
    else:
        app.setStyleSheet(qdarktheme.load_stylesheet("dark"))

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = SpotDLApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
