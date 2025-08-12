from dataclasses import dataclass

from ...discovery.model.descriptor import PluginDescriptor


@dataclass(frozen=True)
class LoadFailure:
    descriptor: PluginDescriptor
    reason: str
    detail: str = ""
