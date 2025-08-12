from pathlib import Path
from typing import TypeVar, OrderedDict

from .json_discoverer import JsonDiscoverer
from .manifest_to_descriptor import ManifestToDescriptor
from .model.descriptor import PluginDescriptor
from .model.rejection import Rejection
from .model.report import DiscoveryReport
from ...constants import COMMON_LOGGING_PREFIX
from ...logging import HoornLogger

T = TypeVar('T')

class PluginDiscoverer:
    """
    High-level façade that:
      1) finds manifest files (JSON),
      2) validates + converts them to descriptors,
      3) deduplicates by descriptor.identity,
      4) returns a deterministic DiscoveryReport.

    Loading/registration are separate concerns.
    """

    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Plugins.PluginDiscoverer"

        self._json_discoverer = JsonDiscoverer(logger)
        self._converter = ManifestToDescriptor(logger)

        self._logger.trace("Initialized.", separator=self._separator)

    def discover_plugins_json(self, root: Path, manifest_name: str) -> DiscoveryReport:
        """
        Discovers plugins through JSON manifest files.

        Args:
            root (Path): Root directory of plugins directory.
            manifest_name (str): Manifest file name (including json extension).

        Returns:
            A DiscoveryReport object.
        """

        candidates = self._json_discoverer.discover(root, manifest_name)

        accepted_map: OrderedDict[tuple[str, str, str], PluginDescriptor] = OrderedDict[tuple[str, str, str], PluginDescriptor]()
        rejected_list: list[Rejection] = []

        for cand in candidates:
            desc, rej = self._converter.convert(cand)
            if rej is not None:
                self._logger.warning(f"Rejected: {rej.manifest_path} — {rej.reason}", separator=self._separator)
                rejected_list.append(rej)
                continue

            assert desc is not None
            key = desc.identity
            if key in accepted_map:
                prev = accepted_map[key]
                self._logger.warning(
                    f"Duplicate plugin identity {key}: keeping first at '{prev.source_path}', ignoring '{desc.source_path}'.",
                    separator=self._separator
                )
                rejected_list.append(Rejection(desc.source_path, f"Duplicate identity {key}"))
                continue

            accepted_map[key] = desc

        # Deterministic ordering for reproducible boots
        accepted = tuple(accepted_map.values())
        rejected = tuple(sorted(rejected_list, key=lambda r: str(r.manifest_path)))

        self._logger.info(
            f"Discovery finished. Accepted: {len(accepted)}; Rejected: {len(rejected)}.",
            separator=self._separator
        )
        return DiscoveryReport(accepted=accepted, rejected=rejected)
