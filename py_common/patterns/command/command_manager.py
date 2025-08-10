from threading import Lock
from typing import List, TypeVar, Tuple

from .command_interface import CommandInterface
from ...constants import COMMON_LOGGING_PREFIX
from ...logging import HoornLogger

T = TypeVar('T')
P = TypeVar('P')

class CommandManager:
    """Component to help with the execution of commands."""
    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._separator = f"{COMMON_LOGGING_PREFIX}.CommandManager"
        self._logger.trace("Successfully initialized.", separator=self._separator)

        self._command_history: List[Tuple[CommandInterface, T]] = []

        self._lock = Lock()

    def execute_command(self, command: CommandInterface, arguments: T) -> P:
        results = command.execute(arguments)

        with self._lock:
            self._command_history.append((command, results))

        return results

    def unexecute_last_command(self) -> None:
        with self._lock:
            last_command = self._command_history.pop()

        last_command[0].unexecute(last_command[1])
