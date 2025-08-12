from pathlib import Path
from typing import Tuple

from .model.candidate import PluginCandidate
from ...constants import COMMON_LOGGING_PREFIX
from ...logging import HoornLogger


class JsonDiscoverer:
    """
    Finds JSON manifests named `<manifest_name>.json` under a root directory.
    """

    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Plugins.JsonDiscoverer"

        self._logger.trace("Initialized.", separator=self._separator)

    def discover(self, root: Path, manifest_name: str) -> Tuple[PluginCandidate, ...]:
        found: list[PluginCandidate] = []

        for p in sorted(root.rglob(manifest_name)):
            if p.is_file():
                self._logger.debug(f"Found manifest: {p}", separator=self._separator)
                found.append(PluginCandidate(manifest_path=p))

        self._logger.info(
            f"Discovery complete under '{root}'. Found: {len(found)} manifests.",
            separator=self._separator
        )

        return tuple(found)
