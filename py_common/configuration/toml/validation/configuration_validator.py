from pathlib import Path
from typing import Any, Dict

from ..loading.load_configuration import ConfigurationLoader
from ..model.schema import TomlConfigurationSchema, TomlConfigurationSchemaElement, TomlConfigurationSchemaSection
from ....constants import COMMON_LOGGING_PREFIX
from ....logging import HoornLogger


class ConfigurationValidator:
    def __init__(self, logger: HoornLogger, configuration_loader: ConfigurationLoader):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Configuration.Validator"
        self._configuration_loader = configuration_loader

    def validate(self, schema: TomlConfigurationSchema, configuration: Dict[str, Any] | Path) -> bool:
        """
        Validates a configuration against a schema.

        Args:
            schema: The TomlConfigurationSchema to validate against.
            configuration: The configuration dictionary or Path to a .toml file.

        Returns:
            True if the configuration is valid, False otherwise.
        """
        if isinstance(configuration, Path):
            config_data = self._configuration_loader.load(configuration)

            if config_data is None:
                return False
        else:
            config_data = configuration

        results = []

        for element_schema in schema.elements:
            results.append(self._validate_element(element_schema, config_data, parent_key=""))

        for section_schema in schema.sections:
            results.append(self._validate_section(section_schema, config_data, parent_key=""))

        results.append(self._validate_metadata(schema, config_data))

        defined_keys = {el.name for el in schema.elements} | {sec.name for sec in schema.sections}
        extra_keys = set(config_data.keys()) - defined_keys
        if extra_keys:
            self._logger.warning(f"Unknown top-level keys found in configuration: {', '.join(extra_keys)}",
                                 separator=self._separator)

        return all(results)

    def _validate_metadata(self, schema: TomlConfigurationSchema, config_data: Dict[str, Any]) -> bool:
        if "version" not in config_data:
            return False

        if schema.version != config_data["version"]:
            self._logger.debug(f"Schema version '{schema.version}' does not match configuration version '{config_data['version']}'")
            return False

        return True

    # noinspection t
    def _validate_section(self, section_schema: TomlConfigurationSchemaSection, config_data: Dict[str, Any], parent_key: str) -> bool:
        """Recursively validates a configuration section."""
        current_key = f"{parent_key}.{section_schema.name}" if parent_key else section_schema.name

        # Check if section exists
        if section_schema.name not in config_data:
            if section_schema.required:
                self._logger.error(f"Required section '{current_key}' is missing.", separator=self._separator)
                return False
            return True

        section_data = config_data[section_schema.name]

        # Check if the section is a table (dictionary)
        if not isinstance(section_data, dict):
            self._logger.error(f"Section '{current_key}' must be a table, but found type '{type(section_data).__name__}'.",
                               separator=self._separator)
            return False

        results = []
        # Validate all elements within this section
        for element_schema in section_schema.elements:
            results.append(self._validate_element(element_schema, section_data, parent_key=current_key))

        # Recursively validate sub-sections
        for sub_section_schema in section_schema.sub_sections:
            results.append(self._validate_section(sub_section_schema, section_data, parent_key=current_key))

        # Check for unknown keys within the section
        defined_keys = {el.name for el in section_schema.elements} | {sec.name for sec in section_schema.sub_sections}
        extra_keys = set(section_data.keys()) - defined_keys
        if extra_keys:
            self._logger.warning(f"Unknown keys found in section '{current_key}': {', '.join(extra_keys)}",
                                 separator=self._separator)

        return all(results)

    # noinspection t
    def _validate_element(self, element_schema: TomlConfigurationSchemaElement, config_data: Dict[str, Any], parent_key: str) -> bool:
        """Validates a single configuration element (key-value pair)."""
        current_key = f"{parent_key}.{element_schema.name}" if parent_key else element_schema.name

        # Check if element exists
        if element_schema.name not in config_data:
            if element_schema.required:
                self._logger.error(f"Required key '{current_key}' is missing.", separator=self._separator)
                return False
            return True

        value = config_data[element_schema.name]

        # Check type
        if element_schema.type and not isinstance(value, element_schema.type):
            self._logger.error(f"Key '{current_key}' has wrong type. "
                               f"Expected '{element_schema.type.__name__}' but got '{type(value).__name__}'.",
                               separator=self._separator)
            return False

        # Check against allowed values
        if element_schema.allowed and value not in element_schema.allowed:
            self._logger.error(f"Key '{current_key}' has value '{value}' which is not in the allowed list: "
                               f"{element_schema.allowed}", separator=self._separator)
            return False

        return True
