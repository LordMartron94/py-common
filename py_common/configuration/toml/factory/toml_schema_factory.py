from typing import Any, Dict

from ..model.schema import TomlConfigurationSchemaSection, TomlConfigurationSchema, TomlConfigurationSchemaElement
from ....constants import COMMON_LOGGING_PREFIX
from ....logging import HoornLogger


class TomlSchemaFactory:
    """Streamlines the creation of TOML schemas from a dictionary definition."""
    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._separator = f"{COMMON_LOGGING_PREFIX}.Configuration.TomlSchemaFactory"

    def create(self, schema_definition: Dict[str, Any]) -> TomlConfigurationSchema:
        """
        Creates the TomlConfigurationSchema from a dictionary definition.

        Args:
            schema_definition: A dictionary outlining the entire schema.

        Returns:
            A populated TomlConfigurationSchema object.
        """
        self._logger.debug("Starting TOML schema creation.", separator=self._separator)

        version = schema_definition.get("version")
        if not version:
            version = "1.0"
            self._logger.warning(
                "Schema definition missing 'version' key, defaulting to '1.0'.",
                separator=self._separator
            )
        else:
            self._logger.debug(f"Found schema version '{version}'.", separator=self._separator)

        # Process root-level elements
        self._logger.debug("Processing root-level elements.", separator=self._separator)
        root_elements_def = schema_definition.get("elements", {})
        root_elements = [
            self._create_element(name, definition)
            for name, definition in root_elements_def.items()
        ]

        # Process top-level sections
        self._logger.debug("Processing top-level sections.", separator=self._separator)
        sections_def = schema_definition.get("sections", {})
        sections = [
            self._create_section(name, definition)
            for name, definition in sections_def.items()
        ]

        schema = TomlConfigurationSchema(
            version=version,
            elements=root_elements,
            sections=sections
        )

        self._logger.info(
            f"Successfully created TOML configuration schema version '{schema.version}'.",
            separator=self._separator
        )
        return schema

    def _create_section(self, name: str, definition: Dict[str, Any]) -> TomlConfigurationSchemaSection:
        """Recursively creates a schema section and its contents."""
        section_separator = f"{self._separator}.Section.{name}"
        self._logger.debug(f"Creating section '{name}'.", separator=section_separator)

        elements_def = definition.get("elements", {})
        elements = [
            self._create_element(el_name, el_def)
            for el_name, el_def in elements_def.items()
        ]

        # Recursive call for sub-sections
        sub_sections_def = definition.get("sub-sections", {})
        sub_sections = [
            self._create_section(sub_name, sub_def)
            for sub_name, sub_def in sub_sections_def.items()
        ]

        self._logger.debug(
            f"Finished creating section '{name}' with {len(elements)} elements and {len(sub_sections)} sub-sections.",
            separator=section_separator
        )

        return TomlConfigurationSchemaSection(
            name=name,
            required=definition.get("required", False),
            elements=elements,
            sub_sections=sub_sections
        )

    def _create_element(self, name: str, definition: Dict[str, Any]) -> TomlConfigurationSchemaElement:
        """Creates a schema element from its definition."""
        self._logger.debug(f"Creating element '{name}'.", separator=f"{self._separator}.Element")

        return TomlConfigurationSchemaElement(
            name=name,
            required=definition.get("required", False),
            type=definition.get("type"),
            default=definition.get("default"),
            allowed=definition.get("allowed")
        )
