import dataclasses
from typing import Type, List, Dict, Any, get_type_hints, Optional

from ..mapping.key_mapping_converter import get_model_key
from ..model.schema import TomlConfigurationSchema, TomlConfigurationSchemaSection, TomlConfigurationSchemaElement
from ....constants import COMMON_LOGGING_PREFIX
from ....logging import HoornLogger


class SchemaModelValidationError(ValueError):
    """Custom exception for schema-to-model validation errors."""
    pass

class SchemaModelValidator:
    """Validates that a dataclass model correctly matches a TOML schema."""
    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._separator = f"{COMMON_LOGGING_PREFIX}.Configuration.SchemaModelValidator"

    def validate(self, schema: TomlConfigurationSchema, model_class: Type, key_mapping: Dict[str, str] | None):
        """
        Validates a schema against a dataclass model.

        Args:
            schema: The TomlConfigurationSchema instance.
            model_class: The dataclass type to validate against.
            key_mapping: Optional mapping of schema keys to model keys.

        Raises:
            SchemaModelValidationError: If the model does not match the schema.
        """
        self._logger.debug(f"Starting validation of schema '{schema.version}' against model '{model_class.__name__}'.", separator=self._separator)
        errors = []

        # We start the recursive validation from the top-level schema and model
        self._validate_recursive(
            schema_part=schema,
            model_class=model_class,
            errors=errors,
            key_mapping=key_mapping
        )

        if errors:
            error_message = f"Model '{model_class.__name__}' does not match the schema. Found {len(errors)} issues:\n" + "\n".join(f"- {e}" for e in errors)
            self._logger.error(error_message, separator=self._separator)
            raise SchemaModelValidationError(error_message)

        self._logger.info(f"Successfully validated schema against model '{model_class.__name__}'.", separator=self._separator)

    def _validate_recursive(
            self,
            schema_part: TomlConfigurationSchema | TomlConfigurationSchemaSection,
            model_class: Type,
            errors: List[str],
            key_mapping: Optional[Dict[str, str]],
            path: str = ""):
        """
        Orchestrates the validation of a schema part against a dataclass model by calling focused helper methods.
        """
        if model_class is None:
            errors.append(f"Received no model class.")
            return

        if not dataclasses.is_dataclass(model_class):
            errors.append(f"Path '{path or 'root'}': Expected a dataclass, but got type '{model_class.__name__}'.")
            return

        # noinspection PyTypeChecker,PyDataclass
        model_fields = {f.name: f for f in dataclasses.fields(model_class)}
        model_type_hints = get_type_hints(model_class)

        # Delegate validation tasks to specialized helpers
        self._validate_elements(schema_part.elements, model_fields, model_type_hints, errors, key_mapping, path)

        sections = getattr(schema_part, 'sections', getattr(schema_part, 'sub_sections', []))
        self._validate_sections(sections, model_fields, model_type_hints, errors, key_mapping, path)

        self._check_for_extra_fields(model_fields, errors, path)

    # noinspection t
    def _validate_elements(
            self,
            elements: List[TomlConfigurationSchemaElement],
            model_fields: Dict[str, Any],
            model_type_hints: Dict[str, Type],
            errors: List[str],
            key_mapping: Optional[Dict[str, str]],
            path: str):
        """Validates schema elements against the fields of the model."""
        for element in elements:
            current_path = f"{path}.{element.name}" if path else element.name

            model_key = get_model_key(key_mapping, element.name)
            if not self._validate_key(
                    model_key=model_key,
                    configuration_key=element.name,
                    errors=errors,
                    current_path=current_path,
                    model_fields=model_fields,
                    descriptor="Elements"):
                continue

            model_type = model_type_hints.get(model_key)

            if element.type and model_type != element.type:
                errors.append(
                    f"Path '{current_path}': Type mismatch. Schema expects '{element.type}', but model has '{model_type.__name__}'."
                )

            model_fields.pop(model_key)

    def _validate_sections(self,
                           sections: List[TomlConfigurationSchemaSection],
                           model_fields: Dict[str, Any],
                           model_type_hints: Dict[str, Type],
                           errors: List[str],
                           key_mapping: Optional[Dict[str, str]],
                           path: str):
        """Validates schema sections by recursing into nested models."""
        for section in sections:
            current_path = f"{path}.{section.name}" if path else section.name

            model_key = get_model_key(key_mapping, section.name)
            if not self._validate_key(
                    model_key=model_key,
                    configuration_key=section.name,
                    errors=errors,
                    current_path=current_path,
                    model_fields=model_fields,
                    descriptor="Section"):
                continue

            nested_model_class = model_type_hints.get(model_key)
            self._validate_recursive(
                schema_part=section,
                model_class=nested_model_class,
                errors=errors,
                key_mapping=key_mapping,
                path=current_path
            )

            model_fields.pop(model_key)

    @staticmethod
    def _check_for_extra_fields(model_fields: Dict[str, Any], errors: List[str], path: str):
        """Checks for any fields present in the model but not defined in the schema."""
        for extra_field_name in model_fields.keys():
            current_path = f"{path}.{extra_field_name}" if path else extra_field_name
            errors.append(f"Path '{current_path}': Field exists in model but is not defined in the schema.")

    @staticmethod
    def _validate_key(
            model_key: str | None,
            configuration_key: str,
            errors: List[str],
            current_path: str,
            descriptor: str,
            model_fields: Dict[str, Any]) -> bool:
        if model_key is None:
            errors.append(f"Key '{configuration_key}' not found in key mapping.")
            return False

        if model_key not in model_fields:
            errors.append(f"Path '{current_path}': {descriptor} defined in schema is missing in the model.")
            return False

        return True
