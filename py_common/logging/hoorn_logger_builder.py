import platform
from pathlib import Path
from typing import List

from . import HoornLogger, LogType
from .output import HoornLogOutputInterface, FileHoornLogOutput, DefaultHoornLogOutput
from .output.windowed_hoorn_log_output import WindowedHoornLogOutput


def _get_user_local_appdata_dir() -> Path:
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        return home / "AppData" / "Local"
    if system == "Darwin":
        return home / "Library" / "Application Support"
    if system == "Linux":
        return home / ".local" / "share"
    raise ValueError(f"Unsupported OS: {system}")


class HoornLoggerBuilder:
    """Fluent builder for a HoornLogger, using subprocess-based GUI output with batch sizing."""
    def __init__(
            self,
            application_name_sanitized: str,
            max_separator_length: int = 30,
            allow_disable: bool = False,
    ):
        self._app_name = application_name_sanitized
        self._max_sep = max_separator_length
        self._allow_disable = allow_disable
        self._outputs: List[HoornLogOutputInterface] = []

    def build_file_based_output(
            self,
            create_directory: bool = True,
            use_combined: bool = True,
            max_logs_to_keep: int = 10,
            buffer_limit: int = 25000,
    ) -> "HoornLoggerBuilder":
        file_out = FileHoornLogOutput(
            log_directory=_get_user_local_appdata_dir() / self._app_name / "logs" / "Components",
            max_logs_to_keep=max_logs_to_keep,
            max_separator_length=self._max_sep,
            buffer_limit=buffer_limit,
            create_directory=create_directory,
            use_combined=use_combined,
        )
        self._outputs.append(file_out)
        return self

    def build_console_output(self) -> "HoornLoggerBuilder":
        console_out = DefaultHoornLogOutput(max_separator_length=self._max_sep)
        self._outputs.append(console_out)
        return self

    def build_gui_output(
            self,
    ) -> "HoornLoggerBuilder":
        """
        Adds a subprocess-based PyQt GUI output with dynamic batch sizing.
        """
        gui_out = WindowedHoornLogOutput(
            max_separator_length=self._max_sep
        )
        self._outputs.append(gui_out)
        return self

    def get_logger(self, min_level: LogType) -> HoornLogger:
        if not self._allow_disable and not self._outputs:
            raise ValueError("At least one output must be built before getting a logger.")

        return HoornLogger(
            outputs=self._outputs,
            min_level=min_level,
            separator_root=self._app_name,
            max_separator_length=self._max_sep,
        )
