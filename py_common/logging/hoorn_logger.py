import threading
from typing import List, Union

from colorama import init

from ..logging.factory.hoorn_log_factory import HoornLogFactory
from ..logging.log_type import LogType
from ..logging.output.default_hoorn_log_output import DefaultHoornLogOutput
from ..logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class HoornLogger:
    def __init__(
            self,
            outputs: Union[List[HoornLogOutputInterface], None] = None,
            min_level: LogType = LogType.INFO,
            separator_root: str = "",
            max_separator_length: int = 30,
    ):
        """
        Initializes a new instance of the HoornLogger class.
        :param outputs: The output methods to use.
        Defaults to :class:`DefaultHoornLogOutput` which is the console.
        :param min_level: The minimum log level to output.
        Defaults to :class:`LogType.INFO`.
        """
        # initialize Colorama
        init(autoreset=True)

        # set up outputs
        if outputs is None or len(outputs) == 0:
            outputs = [DefaultHoornLogOutput(max_separator_length=max_separator_length)]

        self._outputs = outputs
        self._min_level = min_level
        self._separator_root = separator_root
        self._log_factory = HoornLogFactory(max_separator_length=max_separator_length)
        self._log_output_lock: threading.Lock = threading.Lock()

        # dynamically stub out disabled methods
        self._initialize_log_stubs()

    def _initialize_log_stubs(self) -> None:
        """
        Replace disabled log-level methods with no-op stubs that still honor force_show.
        """
        # Capture original methods
        _real = {
            'trace': self.trace,
            'debug': self.debug,
            'info': self.info,
            'warning': self.warning,
            'error': self.error,
            'critical': self.critical,
        }

        # For each level, if disabled, override with stub
        for level_name, method in _real.items():
            level = LogType[level_name.upper()]
            if level < self._min_level:
                # define stub in closure
                def make_stub(orig, _):
                    def stub(message: str,
                             force_show: bool = False,
                             encoding: str = "utf-8",
                             separator: str = None) -> None:
                        if force_show:
                            orig(message, force_show=True, encoding=encoding, separator=separator)
                        else: return
                    return stub

                setattr(self, level_name, make_stub(method, level))

    def save(self) -> None:
        """Saves the logs for each applicable output."""
        for output in self._outputs:
            output.save()

    def set_min_level(self, min_level: LogType) -> None:
        """
        Sets the minimum log level to output.
        :param min_level: The minimum log level to output.
        """
        self._min_level = min_level
        self._initialize_log_stubs()

    def _log(
            self,
            log_type: LogType,
            message: str,
            encoding: str,
            separator: str = None,
    ) -> None:
        hoorn_log = self._log_factory.create_hoorn_log(
            log_type,
            message,
            separator=self._separator_root + f".{separator}" if separator else self._separator_root,
        )

        with self._log_output_lock:
            for output in self._outputs:
                output.output(hoorn_log, encoding=encoding)

    # Logging methods
    def trace(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        self._log(LogType.TRACE, message, encoding=encoding, separator=separator)

    def debug(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        self._log(LogType.DEBUG, message, encoding=encoding, separator=separator)

    def info(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        self._log(LogType.INFO, message, encoding=encoding, separator=separator)

    def warning(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        self._log(LogType.WARNING, message, encoding=encoding, separator=separator)

    def error(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        self._log(LogType.ERROR, message, encoding=encoding, separator=separator)

    def critical(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        self._log(LogType.CRITICAL, message, encoding=encoding, separator=separator)
