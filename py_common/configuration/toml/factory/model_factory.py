import dataclasses
from itertools import chain
from pathlib import Path
from typing import Type, Any, Dict, TypeVar, get_type_hints

from ..loading.load_configuration import ConfigurationLoader
from ..model.schema import TomlConfigurationSchema, TomlConfigurationSchemaSection, TomlConfigurationSchemaElement
from ....constants import COMMON_LOGGING_PREFIX
from ....logging import HoornLogger

T = TypeVar('T')

class ConfigurationModelAssemblyError(ValueError):
    pass

class ConfigurationModelFactory:
    """Creates a configuration model from data, applying defaults from a schema for missing fields."""

    _SENTINEL = object()

    def __init__(self, logger: HoornLogger, configuration_loader: ConfigurationLoader):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Configuration.ModelFactory"
        self._configuration_loader = configuration_loader
        self._reverse_key_mapping: Dict[str, str] = {}

    def create(self,
               configuration: Dict[str, Any] | Path,
               associated_model: Type[T],
               schema: TomlConfigurationSchema,
               key_mapping: Dict[str, str] | None) -> T:
        """Loads config and recursively creates a model instance, applying schema defaults."""
        self._logger.debug(f"Creating configuration model for {associated_model.__name__}.", separator=self._separator)

        # Create a reverse mapping for efficient lookups
        self._reverse_key_mapping = {v: k for k, v in key_mapping.items()} if key_mapping else {}
        config_data = self._get_config_data(configuration)

        return self._instantiate_recursively(associated_model, config_data, schema)

    def _get_config_data(self, configuration: Dict[str, Any] | Path) -> Dict[str, Any]:
        """Loads configuration data from a Path or returns it if it's already a dictionary."""
        if isinstance(configuration, Path):
            return self._configuration_loader.load(configuration)
        return configuration

    def _get_config_key(self, model_key: str) -> str:
        """Finds the original schema/config key that corresponds to a model's field name."""
        return self._reverse_key_mapping.get(model_key, model_key)

    @staticmethod
    def _find_schema_definition(schema_part: TomlConfigurationSchema | TomlConfigurationSchemaSection,
                                config_key: str) -> TomlConfigurationSchemaElement | TomlConfigurationSchemaSection | None:
        all_definitions = chain(
            schema_part.elements,
            getattr(schema_part, 'sections', []),
            getattr(schema_part, 'sub_sections', [])
        )

        for definition in all_definitions:
            if definition.name == config_key:
                return definition

        return None

    def _instantiate_recursively(self,
                                 model_class: Type[T],
                                 data: Dict[str, Any],
                                 schema_part: TomlConfigurationSchema | TomlConfigurationSchemaSection) -> T:
        """
        Instantiates a dataclass by gathering constructor arguments and handling final errors.
        This is the main orchestrator for the recursive build process.
        """
        constructor_args = self._gather_constructor_args(model_class, data, schema_part)

        try:
            return model_class(**constructor_args)
        except TypeError as e:
            msg = (f"Failed to create model for {model_class.__name__}. A required field might be "
                   f"missing from both the config and the schema defaults: {e}.")
            self._logger.error(msg, separator=self._separator)
            raise ConfigurationModelAssemblyError(msg) from e

    def _gather_constructor_args(self,
                                 model_class: Type[T],
                                 data: Dict[str, Any],
                                 schema_part: TomlConfigurationSchema | TomlConfigurationSchemaSection) -> Dict[str, Any]:
        """
        Loops through all fields of a dataclass and resolves the final value for each one.

        Returns:
            A dictionary of arguments ready for the dataclass constructor.
        """
        constructor_args = {}
        type_hints = get_type_hints(model_class)

        for field in dataclasses.fields(model_class):
            field_type = type_hints[field.name]

            value = self._resolve_field_value(field.name, field_type, data, schema_part)

            if value is not self._SENTINEL:
                constructor_args[field.name] = value

        return constructor_args

    def _resolve_field_value(self,
                             model_key: str,
                             field_type: Type,
                             data: Dict[str, Any],
                             schema_part: TomlConfigurationSchema | TomlConfigurationSchemaSection) -> Any:
        """
        Resolves the final value for a single field by checking the config data first,
        then falling back to the schema's default value.
        (Refactored to handle defaults correctly).
        """
        config_key = self._get_config_key(model_key)

        if config_key in data:
            raw_value = data[config_key]
            return self._process_config_value(field_type, raw_value, config_key, schema_part)

        schema_def = self._find_schema_definition(schema_part, config_key)

        if isinstance(schema_def, TomlConfigurationSchemaElement) and schema_def.default is not None:
            return schema_def.default

        return self._SENTINEL

    def _process_config_value(self,
                              field_type: Type,
                              raw_value: Any,
                              config_key: str,
                              schema_part: TomlConfigurationSchema | TomlConfigurationSchemaSection) -> Any:
        """
        Processes a raw value that was found in the configuration data.
        It handles nested dataclasses by recursing.
        """
        # If the field is a dataclass and the data is a dict, we need to recurse.
        if dataclasses.is_dataclass(field_type) and isinstance(raw_value, dict):
            nested_schema_def = self._find_schema_definition(schema_part, config_key)
            if nested_schema_def:
                return self._instantiate_recursively(field_type, raw_value, nested_schema_def)
            return self._SENTINEL

        return raw_value
