from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodeEntry:
    """
    Where to load the plugin code from and which attribute to call.
    """
    type: str
    path: Path
    attr: str = "register"
