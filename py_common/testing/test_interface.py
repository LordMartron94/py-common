import abc
from abc import abstractmethod

from ..constants import COMMON_LOGGING_PREFIX
from ..exceptions.interface_exceptions import InterfaceInstantiationException
from ..logging import HoornLogger


class TestInterface(abc.ABC):
    """Represents a test interface."""
    def __init__(self, logger: HoornLogger, is_child: bool = False):
        if not is_child:
            raise InterfaceInstantiationException(logger, separator=f"{COMMON_LOGGING_PREFIX}.TestInterface")

        self._logger = logger

    @abstractmethod
    def test(self, **kwargs) -> None:
        """Performs the modularized test."""
