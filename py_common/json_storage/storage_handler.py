import json
from pathlib import Path
from typing import Any, Optional, Union

from ..logging import HoornLogger


class JsonStorageHandler:
    """Provides an API for handling JSON storage."""

    def __init__(self, logger: "HoornLogger", file_path: Path, allow_non_exist: bool = False):
        self._logger: "HoornLogger" = logger
        self._file_path: Path = file_path
        self._separator: str = "Common.JsonStorageHandling"
        self._validate_json_path(file_path, allow_non_exist)
        self._logger.debug(
            f"Successfully initialized JSON storage handler with path: \"{str(file_path)}\"",
            separator=self._separator
        )

    def _validate_json_path(self, file_path: Path, allow_non_exist: bool = False):
        """Validate that the provided file path exists and is a valid JSON file."""
        if (not allow_non_exist) and (not file_path.exists()):
            self._logger.error(
                f"File path does not exist: \"{str(file_path)}\"",
                separator=self._separator
            )
            raise FileNotFoundError(f"File path does not exist: {file_path}")

        if (not allow_non_exist) and (not file_path.is_file()):
            self._logger.error(
                f"Provided path is not a file: \"{str(file_path)}\"",
                separator=self._separator
            )
            raise IsADirectoryError(f"Provided path is not a file: {file_path}")

        if file_path.suffix.lower() != ".json":
            self._logger.error(
                f"File extension is not .json: \"{str(file_path)}\"",
                separator=self._separator
            )
            raise ValueError(f"File extension is not .json: {file_path}")

        self._logger.debug(
            f"Validated JSON file path: \"{str(file_path)}\"",
            separator=self._separator
        )

    def read(self) -> Optional[Union[dict, list]]:
        """Reads and returns the contents of the JSON file."""
        try:
            with self._file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._logger.debug("Successfully read JSON data from file.", separator=self._separator)
            return data
        except Exception as e:
            self._logger.error(f"Failed to read JSON file: {e}", separator=self._separator)
            return None

    def write(self, data: Union[dict, list]) -> bool:
        """Writes data to the JSON file, creating necessary directories."""
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            with self._file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self._logger.debug("Successfully wrote JSON data to file.", separator=self._separator)
            return True
        except Exception as e:
            self._logger.error(f"Failed to write JSON file: {e}", separator=self._separator)
            return False

    def append(self, new_data: Any) -> bool:
        """Appends data to the existing JSON structure."""
        current_data = self.read()
        if current_data is None:
            self._logger.info("File not found or empty. Creating new file.", separator=self._separator)
            return self.write(new_data)

        try:
            if isinstance(current_data, list):
                if isinstance(new_data, list):
                    current_data.extend(new_data)
                else:
                    current_data.append(new_data)
            elif isinstance(current_data, dict) and isinstance(new_data, dict):
                current_data.update(new_data)
            else:
                self._logger.error("Incompatible data types for appending.", separator=self._separator)
                return False

            return self.write(current_data)
        except Exception as e:
            self._logger.error(f"Failed to append data: {e}", separator=self._separator)
            return False

    def clear(self) -> bool:
        """Clears the contents of the JSON file."""
        return self.write({})

    def exists(self) -> bool:
        """Checks if the JSON file exists."""
        existence = self._file_path.exists()
        self._logger.trace(f"File exists: {existence}", separator=self._separator)
        return existence

    def delete(self) -> bool:
        """Deletes the JSON file if it exists."""
        if not self.exists():
            self._logger.warning("Attempted to delete non-existent file.", separator=self._separator)
            return False
        try:
            self._file_path.unlink()
            self._logger.info("Successfully deleted JSON file.", separator=self._separator)
            return True
        except Exception as e:
            self._logger.error(f"Failed to delete file: {e}", separator=self._separator)
            return False
