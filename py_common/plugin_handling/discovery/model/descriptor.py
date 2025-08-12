from dataclasses import field, dataclass
from pathlib import Path
from typing import Tuple, Dict, Any


@dataclass(frozen=True)
class PluginDescriptor:
    """
    Immutable identity + minimal metadata for a discovered plugin.
    Hashable for deduplication; identity is (name, version, api_version).
    """
    name: str
    version: str
    api_version: str
    capabilities: Tuple[str, ...] = field(default_factory=tuple)
    source_path: Path = Path()
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def identity(self) -> Tuple[str, str, str]:
        return self.name.lower(), self.version, self.api_version
