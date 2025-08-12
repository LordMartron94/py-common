from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rejection:
    """Why a candidate was rejected."""
    manifest_path: Path
    reason: str
