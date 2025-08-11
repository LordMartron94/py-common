import dataclasses
from pathlib import Path
from typing import Type, Any, Dict, TypeVar, get_type_hints

from ..loading.load_configuration import ConfigurationLoader
from ..mapping.key_mapping_converter import get_model_key
from ....constants import COMMON_LOGGING_PREFIX
from ....logging import HoornLogger

T = TypeVar('T')

class ConfigurationModelAssemblyError(ValueError):
    pass

class ConfigurationModelFactory:
    """Creates a configuration model from configuration data, handling nested dataclasses."""
    def __init__(self, logger: HoornLogger, configuration_loader: ConfigurationLoader):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Configuration.ModelFactory"
        self._configuration_loader = configuration_loader

    def create(self, configuration: Dict[str, Any] | Path, associated_model: Type[T], key_mapping: Dict[str, str] | None) -> T:
        """Loads configuration and recursively creates an instance of the associated model."""
        self._logger.debug(f"Creating configuration model for {associated_model.__name__}.", separator=self._separator)

        config_data = self._get_config_data(configuration)

        return self._instantiate_recursively(associated_model, config_data, key_mapping)

    def _get_config_data(self, configuration: Dict[str, Any] | Path) -> Dict[str, Any]:
        """Loads configuration data from a Path or returns it if it's already a dictionary."""
        if isinstance(configuration, Path):
            return self._configuration_loader.load(configuration)
        return configuration

    # noinspection t
    def _instantiate_recursively(self, model_class: Type[T], data: Dict[str, Any], key_mapping: Dict[str, str] | None) -> T:
        """Recursively builds a dataclass instance from a dictionary."""
        try:
            constructor_args = {}
            type_hints = get_type_hints(model_class)

            for config_key, value in data.items():
                model_key = get_model_key(key_mapping, config_key)

                if model_key not in type_hints:
                    continue

                field_type = type_hints[model_key]

                if dataclasses.is_dataclass(field_type) and isinstance(value, dict):
                    constructor_args[model_key] = self._instantiate_recursively(field_type, value, key_mapping)
                else:
                    constructor_args[model_key] = value

            return model_class(**constructor_args)

        except TypeError as e:
            msg = f"Failed to create model for {model_class.__name__}. Check for missing values or type mismatches: {e}."
            self._logger.error(msg, separator=self._separator)
            raise ConfigurationModelAssemblyError(msg) from e
