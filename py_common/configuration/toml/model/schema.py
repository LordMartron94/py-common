import dataclasses
from typing import Type, Any, Optional, List


@dataclasses.dataclass(frozen=True)
class TomlConfigurationSchemaElement:
    name: str
    required: bool
    type: Type = None
    default: Optional[Any] = None
    allowed: Optional[List[Any]] = None

@dataclasses.dataclass(frozen=True)
class TomlConfigurationSchemaSection:
    name: str
    required: bool
    elements: List[TomlConfigurationSchemaElement]
    sub_sections: List["TomlConfigurationSchemaSection"]

@dataclasses.dataclass(frozen=True)
class TomlConfigurationSchema:
    version: str
    sections: List[TomlConfigurationSchemaSection]
    elements: List[TomlConfigurationSchemaElement]
