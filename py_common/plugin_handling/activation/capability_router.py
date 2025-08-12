from typing import Mapping, Dict, Any

from .protocol.capability_activator import CapabilityActivator
from ...constants import COMMON_LOGGING_PREFIX
from ...logging import HoornLogger


class CapabilityRouter:
    """Maps capability keys to activators and dispatches activation."""
    def __init__(self, logger: HoornLogger, activators: list[CapabilityActivator]):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Plugins.Activation"
        self._by_key: Dict[str, CapabilityActivator] = {a.key: a for a in activators}

    def activate_all(self, exports: Mapping[str, Any]) -> None:
        """
        Activates all exports.

        Args:
            exports: A mapping of export keys to objects.
        """

        for key in sorted(exports.keys()):
            export = exports[key]
            activator = self._by_key.get(key)
            if activator is None:
                self._logger.debug(f"No activator for capability '{key}'; ignoring.", separator=self._separator)
                continue
            activator.activate(export)
