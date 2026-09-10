import os
import json
from PyQt6.QtWidgets import QMessageBox


class SettingsManagerMixin:
    """Mixin untuk manajemen pengaturan persistent (config.json) dan event sinkronisasi opsi."""

    def on_setting_changed(self):
        self.update_command_preview()
        self.save_settings()

    def save_settings(self):
        """Menyimpan konfigurasi ke config.json agar tidak perlu diatur ulang setiap membuka app."""
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
        """Memuat konfigurasi dari config.json jika ada."""
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
