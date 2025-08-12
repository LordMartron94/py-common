from typing import runtime_checkable, Protocol, Any


@runtime_checkable
class CapabilityActivator(Protocol):
    """One activator per capability key; stateless or lightweight state."""

    @property
    def key(self) -> str: ...

    def activate(self, export: Any) -> None: ...
