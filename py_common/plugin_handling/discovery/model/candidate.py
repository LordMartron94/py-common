from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PluginCandidate:
    """A manifest JSON file found on disk (untrusted input)."""
    manifest_path: Path
