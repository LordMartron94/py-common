from typing import List, Union

from colorama import init

from ..logging.factory.hoorn_log_factory import HoornLogFactory
from ..logging.log_type import LogType
from ..logging.output.default_hoorn_log_output import DefaultHoornLogOutput
from ..logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class HoornLogger:
    def __init__(self, 
                 outputs: Union[List[HoornLogOutputInterface], None] = None,
                 min_level: LogType = LogType.INFO):
        """
        Initializes a new instance of the HoornLogger class.
        :param outputs: The output methods to use.
        Defaults to :class:`DefaultHoornLogOutput` which is the console.
        :param min_level: The minimum log level to output.
        Defaults to :class:`LogType.INFO`.
        """

        init(autoreset=True)

        if outputs is None or len(outputs) == 0:
            outputs = [DefaultHoornLogOutput()]

        self._log_factory = HoornLogFactory()

        self._min_level = min_level
        self._outputs = outputs

    def _can_output(self, log_type: LogType) -> bool:
        return log_type >= self._min_level

    def _log(self, log_type: LogType, message: str, force_show: bool = False) -> None:
        if not force_show and not self._can_output(log_type):
            return

        hoorn_log = self._log_factory.create_hoorn_log(log_type, message)

        for output in self._outputs:
            output.output(hoorn_log)

    def debug(self, message: str, force_show: bool = False) -> None:
        self._log(LogType.DEBUG, message, force_show)

    def info(self, message: str, force_show: bool = False) -> None:
        self._log(LogType.INFO, message, force_show)

    def warning(self, message: str, force_show: bool = False) -> None:
        self._log(LogType.WARNING, message, force_show)

    def error(self, message: str, force_show: bool = False) -> None:
        self._log(LogType.ERROR, message, force_show)

    def critical(self, message: str, force_show: bool = False) -> None:
        self._log(LogType.CRITICAL, message, force_show)
