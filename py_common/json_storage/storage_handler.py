import json
from pathlib import Path
from typing import Any, Optional, Union

from ..logging import HoornLogger


class JsonStorageHandler:
    """Provides an API for handling JSON storage."""

    def __init__(self, logger: "HoornLogger", file_path: Path):
        self._logger: "HoornLogger" = logger
        self._file_path: Path = file_path
        self._separator: str = "Common.JsonStorageHandling"
        self._logger.debug(
            f"Successfully initialized JSON storage handler with path: \"{str(file_path)}\"",
            separator=self._separator
        )

    def read(self) -> Optional[Union[dict, list]]:
        """Reads and returns the contents of the JSON file."""
        if not self._file_path.exists():
            self._logger.warning(
                f"Tried to read non-existent file: \"{self._file_path}\"",
                separator=self._separator
            )
            return None
        try:
            with self._file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self._logger.debug("Successfully read JSON data from file.", separator=self._separator)
            return data
        except Exception as e:
            self._logger.error(f"Failed to read JSON file: {e}", separator=self._separator)
            return None

    def write(self, data: Union[dict, list]) -> bool:
        """Overwrites the JSON file with the provided data. Creates file and parent directories if they don't exist."""
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
        """
        Appends data to the existing JSON structure.
        If the file contains a list, appends to it.
        If the file contains a dict, merges keys (new_data must be a dict).
        """
        current_data = self.read()

        if current_data is None:
            self._logger.info("File did not exist or was empty. Creating new file with provided data.",
                              separator=self._separator)
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
                self._logger.error("Incompatible types for appending to JSON file.", separator=self._separator)
                return False

            return self.write(current_data)
        except Exception as e:
            self._logger.error(f"Failed to append data: {e}", separator=self._separator)
            return False

    def clear(self) -> bool:
        """Clears the contents of the JSON file (writes empty dict)."""
        try:
            with self._file_path.open("w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
            self._logger.info("Successfully cleared JSON file.", separator=self._separator)
            return True
        except Exception as e:
            self._logger.error(f"Failed to clear JSON file: {e}", separator=self._separator)
            return False

    def exists(self) -> bool:
        """Returns whether the file exists."""
        existence = self._file_path.exists()
        self._logger.trace(f"Checked existence: {existence}", separator=self._separator)
        return existence

    def delete(self) -> bool:
        """Deletes the JSON file if it exists."""
        if not self._file_path.exists():
            self._logger.warning("Attempted to delete a file that does not exist.", separator=self._separator)
            return False
        try:
            self._file_path.unlink()
            self._logger.info("Successfully deleted JSON file.", separator=self._separator)
            return True
        except Exception as e:
            self._logger.error(f"Failed to delete file: {e}", separator=self._separator)
            return False
