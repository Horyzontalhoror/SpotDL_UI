import shlex
from PyQt6.QtWidgets import QApplication


class CommandBuilderMixin:
    """Mixin untuk membangun sintaks perintah CLI SpotDL dan preview template."""

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
