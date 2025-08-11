from pathlib import Path
from typing import Type, Any, Dict, TypeVar

from ..loading.load_configuration import ConfigurationLoader
from ..mapping.key_mapping_converter import get_model_key
from ....constants import COMMON_LOGGING_PREFIX
from ....logging import HoornLogger

T = TypeVar('T')

class ConfigurationModelAssemblyError(ValueError):
    pass

class ConfigurationModelFactory:
    """Creates a configuration model from configuration data."""
    def __init__(self, logger: HoornLogger, configuration_loader: ConfigurationLoader):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Configuration.ModelFactory"
        self._configuration_loader = configuration_loader

    def create(self, configuration: Dict[str, Any] | Path, associated_model: Type, key_mapping: Dict[str, str] | None) -> T:
        self._logger.debug(f"Creating configuration model for model {associated_model.__name__}.", separator=self._separator)

        if isinstance(configuration, Path):
            config_data = self._configuration_loader.load(configuration)
        else:
            config_data = configuration

        try:
            data: Dict[str, Any] = {
                get_model_key(key_mapping, k): v
                for k, v in config_data.items()
            }

            return associated_model(**data)
        except Exception as e:
            msg = f"Failed to create configuration model for model {associated_model.__name__}: {e}."
            self._logger.error(msg, separator=self._separator)
            raise ConfigurationModelAssemblyError(msg)
