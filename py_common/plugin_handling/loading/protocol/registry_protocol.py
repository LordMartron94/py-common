from typing import runtime_checkable, Protocol

from ....logging import HoornLogger


@runtime_checkable
class RegistryProtocol(Protocol):
    """
    Minimal surface the system exposes to plugins during registration.
    """

    @property
    def logger(self) -> HoornLogger: ...
