import tomllib
from pathlib import Path
from typing import Dict, Any

from ....constants import COMMON_LOGGING_PREFIX
from ....exceptions.path_exceptions import PathNotFoundError, PathNotAFileError, PathNotTheRightExtensionError
from ....logging import HoornLogger


class ConfigurationLoader:
    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._separator = f"{COMMON_LOGGING_PREFIX}.Configuration.Loader"

    def load(self, configuration_path: Path) -> Dict[str, Any] | None:
        try:
            self._validate_path(configuration_path)
            with open(configuration_path, "rb") as config_file:
                config_data = tomllib.load(config_file)
                return config_data
        except tomllib.TOMLDecodeError as e:
            self._logger.error(f"Failed to parse TOML file: {e}", separator=self._separator)

        return None

    def _validate_path(self, path: Path):
        """Validates the path to the configuration file."""
        if not path.exists():
            raise PathNotFoundError(self._logger, self._separator, path)

        if not path.is_file():
            raise PathNotAFileError(self._logger, self._separator, path)

        if path.suffix != ".toml":
            raise PathNotTheRightExtensionError(self._logger, self._separator, path, extensions=[".toml"])
