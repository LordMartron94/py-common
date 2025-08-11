from pathlib import Path
from typing import Any, Dict, List, Tuple, Type, TypeVar

from .factory.model_factory import ConfigurationModelFactory
from .factory.toml_schema_factory import TomlSchemaFactory
from .loading.load_configuration import ConfigurationLoader
from .model.schema import TomlConfigurationSchema
from .validation.configuration_validator import ConfigurationValidator
from .validation.model_validator import SchemaModelValidator
from ...constants import COMMON_LOGGING_PREFIX
from ...logging import HoornLogger

T = TypeVar("T")

class UnmatchedSchemaError(ValueError):
    pass

class TomlConfigurationHandler:
    """
    High-Level API to handle TOML configuration for your project.
    """
    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Configuration.TomlConfigurationHandler"

        self._schema_factory: TomlSchemaFactory = TomlSchemaFactory(self._logger)
        self._schema_model_validator: SchemaModelValidator = SchemaModelValidator(self._logger)

        configuration_loader: ConfigurationLoader = ConfigurationLoader(self._logger)

        self._configuration_validator: ConfigurationValidator = ConfigurationValidator(self._logger, configuration_loader)
        self._model_factory: ConfigurationModelFactory = ConfigurationModelFactory(self._logger, configuration_loader)

        self._schemas: List[Tuple[TomlConfigurationSchema, Type[T]]] = []

    #region Schema Definition

    def append_schema_from_dict(self, schema_definition: Dict[str, Any], associated_model: Type[T], key_mapping: Dict[str, str] | None = None) -> "TomlConfigurationHandler":
        """
        Defines the configuration schema using a dictionary.

        Args:
            schema_definition: A dictionary outlining the entire schema.
            associated_model: An object matching the schema keys and types.
            key_mapping: A dictionary mapping schema keys to model keys.

        Returns:
            The handler instance for method chaining.

        Raises:
            SchemaValidationError: If the associated dataclass does not match the schema.
        """
        self._logger.debug("Defining schema from dictionary.", separator=self._separator)

        schema = self._schema_factory.create(schema_definition)

        self._schema_model_validator.validate(schema, associated_model, key_mapping)

        self._schemas.append((schema, associated_model))
        return self

    #endregion

    #region Validation

    def validate_configuration(self, configuration: Dict[str, Any] | Path) -> bool:
        """
        Validates a configuration based on the configured schemas.

        Args:
            configuration: A configuration dictionary or a path to the toml configuration file.

        Returns:
            Whether the configuration was valid.

        Raises:
            RunTimeError: If there are no schemas to validate.
            PathNotFoundError: If the path to the configuration file is not found.
            PathNotAFileError: If the path to the configuration file is not a file.
            PathNotTheRightExtensionError: If the path to the configuration file is not a toml file.
        """
        if len(self._schemas) == 0:
            msg = "No schemas to validate."
            self._logger.error(msg, separator=self._separator)
            raise RuntimeError(msg)

        results: List[bool] = []

        for schema, _ in self._schemas:
            results.append(self._configuration_validator.validate(schema, configuration))

        return any(results)

    #endregion

    #region Loading

    def load_and_instantiate(self,
                             configuration: Dict[str, Any] | Path,
                             key_mapping: Dict[str, str] | None = None) -> T:
        """
        Loads, validates, and instantiates a configuration into its associated data model.

        It iterates through the registered schemas, and for the first one that
        validates the configuration successfully, it populates and returns an
        instance of the corresponding model.

        Args:
            configuration: A configuration dictionary or a path to the TOML file.
            key_mapping: A dictionary mapping schema keys to model keys.

        Returns:
            An instance of the associated data model (e.g., a dataclass)
            populated with the configuration data.

        Raises:
            RuntimeError: If no schemas have been defined.
            ConfigurationValidationError: If the configuration fails to validate
                                        against all registered schemas.
            PathNotFoundError: If the path to the configuration file is not found.
            PathNotAFileError: If the path to the configuration file is not a file.
            PathNotTheRightExtensionError: If the path to the configuration file is not a toml file.
            UnmatchedSchemaError: If there are no matches for the configuration.
            ConfigurationModelAssemblyError: If something went wrong during the creation of the model.
        """
        if not self._schemas:
            raise RuntimeError("Cannot load configuration: No schemas have been defined.")

        for schema, model_class in self._schemas:
            if self._configuration_validator.validate(schema, configuration):
                self._logger.info(f"Configuration validated successfully against schema for model '{model_class.__name__}'.", separator=self._separator)
                return self._model_factory.create(configuration, model_class, schema, key_mapping)

        msg = "Configuration is not valid against any of the registered schemas."
        self._logger.error(msg, separator=self._separator)

        raise UnmatchedSchemaError(msg)

    #endregion
