from graphlib import TopologicalSorter
from typing import Mapping, Dict, Any, Iterable

from .protocol.capability_activator import CapabilityActivator
from ...constants import COMMON_LOGGING_PREFIX
from ...logging import HoornLogger


class CapabilityRouter:
    """
    Maps capability keys to activators and dispatches activation.
    """
    def __init__(self, logger: HoornLogger, *, dependencies: Mapping[str, set[str]] | None = None):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Plugins.Activation"
        self._by_key: Dict[str, CapabilityActivator] = {}
        self._deps: Dict[str, set[str]] = {k: set(v) for k, v in (dependencies or {}).items()}

    def register(self, activator: CapabilityActivator) -> None:
        key = activator.key
        if key in self._by_key:
            self._logger.warning(f"Duplicate activator for '{key}'; keeping the first.", separator=self._separator)
            return
        self._by_key[key] = activator

    def register_many(self, activators: Iterable[CapabilityActivator]) -> None:
        for a in activators:
            self.register(a)

    def activate_all(self, exports: Mapping[str, Any]) -> None:
        """
        Activate all exports in a topologically sorted order by capability key.
        Unknown keys are skipped; missing activators are logged and ignored.
        """
        order = self.topo_order(keys=set(exports.keys()))
        for key in order:
            export = exports.get(key)
            if export is None:
                continue
            act = self._by_key.get(key)
            if act is None:
                self._logger.debug(f"No activator for '{key}'; ignoring.", separator=self._separator)
                continue
            act.activate(export)

    def topo_order(self, keys: set[str]) -> list[str]:
        # Build a subgraph limited to the keys we actually have
        graph: Dict[str, set[str]] = {k: (self._deps.get(k, set()) & keys) for k in keys}
        ts = TopologicalSorter(graph)
        try:
            return list(ts.static_order())
        except Exception as e:
            self._logger.error(f"Capability dependency cycle or invalid graph: {e!r}", separator=self._separator)
            return sorted(keys)
