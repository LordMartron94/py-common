import abc
from typing import TypeVar

from ...logging import HoornLogger
from ...utils.interface_decorator import interface

T = TypeVar('T')
P = TypeVar('P')

@interface()
class CommandInterface(abc.ABC):
    """Defines the contract for each and every command."""
    def __init__(self, logger: HoornLogger):
        self._logger = logger

    @abc.abstractmethod
    def execute(self, arguments: T) -> P:
        """Executes the command."""

    @abc.abstractmethod
    def unexecute(self, arguments: T) -> None:
        """Unexecutes the command."""
