import json
from pathlib import Path
from typing import Dict, Any

from .model.candidate import PluginCandidate
from .model.descriptor import PluginDescriptor
from .model.manifest_schema import ManifestSchema
from .model.rejection import Rejection
from ...constants import COMMON_LOGGING_PREFIX
from ...logging import HoornLogger


class ManifestToDescriptor:
    """
    Converts a candidate manifest file into a validated PluginDescriptor.
    """

    def __init__(self, logger: HoornLogger, schema: ManifestSchema | None = None):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Plugins.ManifestToDescriptor"
        self._schema = schema or ManifestSchema()

        self._logger.trace("Initialized.", separator=self._separator)

    # noinspection t
    def convert(self, candidate: PluginCandidate) -> tuple[PluginDescriptor | None, Rejection | None]:
        p: Path = candidate.manifest_path
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:
            return None, Rejection(p, f"I/O error reading manifest: {e!r}")

        try:
            data: Dict[str, Any] = json.loads(text)
        except Exception as e:
            return None, Rejection(p, f"Invalid JSON: {e!r}")

        s = self._schema

        missing = [k for k in (s.name_key, s.version_key, s.api_version_key) if k not in data]
        if missing:
            return None, Rejection(p, f"Missing required keys: {missing}")

        name = str(data[s.name_key]).strip()
        version = str(data[s.version_key]).strip()
        api_version = str(data[s.api_version_key]).strip()

        if not name or not version or not api_version:
            return None, Rejection(p, "Empty 'name', 'version', or 'api_version'.")

        caps_raw = data.get(s.capabilities_key, [])
        if not isinstance(caps_raw, list) or not all(isinstance(x, str) for x in caps_raw):
            return None, Rejection(p, "'capabilities' must be a list of strings if present.")

        metadata = data.get(s.metadata_key, {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            return None, Rejection(p, "'metadata' must be an object if present.")

        desc = PluginDescriptor(
            name=name,
            version=version,
            api_version=api_version,
            capabilities=tuple(caps_raw),
            source_path=p,
            metadata=metadata,
        )
        return desc, None
