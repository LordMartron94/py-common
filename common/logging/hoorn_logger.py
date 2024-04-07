from typing import List, Union

from colorama import init

from ..logging.factory.hoorn_log_factory import HoornLogFactory
from ..logging.log_type import LogType
from ..logging.output.default_hoorn_log_output import DefaultHoornLogOutput
from ..logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class HoornLogger:
    def __init__(self, outputs: Union[List[HoornLogOutputInterface], None] = None):
        """
        Initializes a new instance of the HoornLogger class.
        :param outputs: The output methods to use. Defaults to `DefaultHoornLogOutput,` which is the console.
        """

        init(autoreset=True)

        if outputs is None or len(outputs) == 0:
            outputs = [DefaultHoornLogOutput()]

        self._log_factory = HoornLogFactory()
        self._outputs = outputs

    def _log(self, log_type: LogType, message: str) -> None:
        hoorn_log = self._log_factory.create_hoorn_log(log_type, message)

        for output in self._outputs:
            output.output(hoorn_log)

    def debug(self, message: str) -> None:
        self._log(LogType.DEBUG, message)

    def info(self, message: str) -> None:
        self._log(LogType.INFO, message)

    def warning(self, message: str) -> None:
        self._log(LogType.WARNING, message)

    def error(self, message: str) -> None:
        self._log(LogType.ERROR, message)

    def critical(self, message: str) -> None:
        self._log(LogType.CRITICAL, message)
