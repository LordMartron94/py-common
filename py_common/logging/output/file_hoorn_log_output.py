import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from ..reserved_keys import RESERVED_LOGGING_KEYS
from ...handlers.file_handler import FileHandler
from ...logging.formatting.log_text_formatter import HoornLogTextFormatter
from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class FileHoornLogOutput(HoornLogOutputInterface):
    def __init__(
            self,
            log_directory: Path,
            max_logs_to_keep: int = 3,
            create_directory: bool = True,
            use_combined: bool = True,
            max_separator_length: int = 30,
            buffer_limit: int = 1000,
    ):
        """
        Formats logs into text files and buffers lines until save is called.

        :param log_directory: The base directory for logs.
        :param max_logs_to_keep: The max number of logs to keep (per directory).
        :param create_directory: Whether to initialize the creation of log directories if they don't exist.
        :param use_combined: Whether to combine multiple separators also into a single log file.
        :param max_separator_length: The maximum length of the separator in the log file names.
        :param buffer_limit: Maximum number of buffered lines before auto-flushing to avoid high memory use.
        """
        self._file_handler: FileHandler = FileHandler()

        self._formatter = HoornLogTextFormatter()
        self._root_log_directory: Path = log_directory
        self._max_logs_to_keep: int = max_logs_to_keep
        self._use_combined: bool = use_combined
        self._max_separator_length: int = max_separator_length
        self._buffer_limit: int = buffer_limit

        # In-memory buffer: maps separator key (str or None) to list of lines
        self._buffers: Dict[Optional[str], List[str]] = {}

        self._validate_directory(self._root_log_directory, create_directory)
        self._increment_logs()

        super().__init__(is_child=True)

    def _validate_directory(self, directory: Path, create_directory: bool):
        if not directory.exists():
            if create_directory:
                directory.mkdir(parents=True, exist_ok=True)
                return

            raise FileNotFoundError(f"Log directory {directory} does not exist")

    def _increment_logs(self) -> None:
        children = self._file_handler.get_children_paths(self._root_log_directory, ".txt", recursive=True)
        organized_by_separator: List[List[Path]] = self._organize_logs_by_subdirectory(children)

        for directory_logs in organized_by_separator:
            matched: List[Tuple[Path, int]] = [
                (path, int(path.stem.split("_")[1])) for path in directory_logs
            ]
            matched.sort(key=lambda x: x[1], reverse=True)
            self._increment_logs_in_directory(matched)

    def _increment_logs_in_directory(self, matched_logs: List[Tuple[Path, int]]) -> None:
        for path, number in matched_logs:
            if number + 1 > self._max_logs_to_keep:
                os.remove(path)
                continue

            new_name = f"log_{number + 1}.txt"
            os.rename(path, path.parent / new_name)

    def _get_path_to_log_to(self, separator: Optional[str] = None) -> Path:
        directory = self._root_log_directory
        if separator:
            directory = directory / separator
            self._validate_directory(directory, True)
        return directory / "log_1.txt"

    def _organize_logs_by_subdirectory(self, log_paths: List[Path]) -> List[List[Path]]:
        log_groups = {}
        for log_path in log_paths:
            parent_dir = log_path.parent.name
            log_groups.setdefault(parent_dir, []).append(log_path)
        return list(log_groups.values())

    def output(self, hoorn_log: HoornLog, encoding: str = "utf-8") -> None:
        formatted = self._formatter.format(hoorn_log)

        # buffer per-separator output
        self._buffer_line(formatted, hoorn_log.separator)

        if self._use_combined and hoorn_log.separator:
            combined = f"[{hoorn_log.separator:<{self._max_separator_length}}] " + self._formatter.format(hoorn_log)
            self._buffer_line(combined, None)

    def _buffer_line(self, line: str, separator: Optional[str]) -> None:
        # strip reserved keys
        for key in RESERVED_LOGGING_KEYS:
            line = line.replace(key, "")

        buf = self._buffers.setdefault(separator, [])
        buf.append(line)
        # auto-flush if exceeded
        if len(buf) >= self._buffer_limit:
            self._flush_buffer(separator)

    def _flush_buffer(self, separator: Optional[str]) -> None:
        # writes buffered lines to file and clears buffer
        lines = self._buffers.get(separator)
        if not lines:
            return
        log_file = self._get_path_to_log_to(separator)
        with open(log_file, "a", encoding="utf-8") as f:
            for ln in lines:
                f.write(ln + "\n")
        self._buffers[separator] = []

    def save(self) -> None:
        """
        Flush all buffered log lines to their respective files.
        """
        for separator in list(self._buffers.keys()):
            self._flush_buffer(separator)
