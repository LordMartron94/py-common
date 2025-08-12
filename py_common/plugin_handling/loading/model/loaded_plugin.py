from dataclasses import dataclass
from typing import Mapping, Any

from ...discovery.model.descriptor import PluginDescriptor


@dataclass(frozen=True)
class LoadedPlugin:
    descriptor: PluginDescriptor
    module_name: str
    exports: Mapping[str, Any]
