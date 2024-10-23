import os
from pathlib import Path

from ...handlers.file_handler import FileHandler
from ...logging.formatting.log_text_formatter import HoornLogTextFormatter
from ...logging.hoorn_log import HoornLog
from ...logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class FileHoornLogOutput(HoornLogOutputInterface):
    def __init__(self, log_directory: Path, max_logs_to_keep: int = 3, create_directory: bool = True):
        self._file_handler: FileHandler = FileHandler()

        self._log_directory: Path = log_directory
        self._max_logs_to_keep: int = max_logs_to_keep

        self._validate_directory(create_directory)

        self._increment_logs()

        self._log_path: Path = self._get_path_to_log_to()

        super().__init__(is_child=True)

    def _validate_directory(self, create_directory: bool):
        if not self._log_directory.exists():
            if create_directory:
                self._log_directory.mkdir(parents=True, exist_ok=True)
                return

            raise FileNotFoundError(f"Log directory {self._log_directory} does not exist")

    def _increment_logs(self) -> None:
        """
        Increments the log number by 1 and removes old logs if necessary.

        :return: None
        """

        children = self._file_handler.get_children_paths(self._log_directory, ".txt")
        children.sort()

        for i in range(len(children)):
            child = children[i]
            if i + 1 > self._max_logs_to_keep:
                os.remove(child)
                continue

            os.rename(child, Path.joinpath(self._log_directory, f"log_{i + 1}.txt"))

    def _get_path_to_log_to(self):
        return Path.joinpath(self._log_directory, f"log_1.txt")

    def _get_number_of_logs_in_directory(self, log_directory: Path) -> int:
        return self._file_handler.get_number_of_files_in_dir(log_directory, ".txt")

    def output(self, hoorn_log: HoornLog, encoding="utf-8") -> None:
        formatter: HoornLogTextFormatter = HoornLogTextFormatter()
        formatted_log: str = formatter.format(hoorn_log)

        with open(self._log_path, "a", encoding=encoding) as f:
            f.write(formatted_log + "\n")
