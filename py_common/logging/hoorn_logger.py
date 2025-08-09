import threading
from typing import List

from colorama import init

from ..logging.factory.hoorn_log_factory import HoornLogFactory
from ..logging.log_type import LogType
from ..logging.output.hoorn_log_output_interface import HoornLogOutputInterface


class HoornLogger:
    def __init__(
            self,
            outputs: List[HoornLogOutputInterface],
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
        """
        Logs a TRACE level message, the most granular level of detail.

        Use this for extremely detailed, high-volume information that tracks the
        step-by-step execution path within a method. It's intended for deep
        debugging of complex algorithms or low-level component interactions.
        This level is typically disabled in production environments.

        Example:
            logger.trace(f"Loop iteration {i}: value is {x}")
            logger.trace("Entering private helper method _calculate_value")
        """
        self._log(LogType.TRACE, message, encoding=encoding, separator=separator)

    def debug(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        """
        Logs a DEBUG level message for detailed diagnostic information.

        Use this to log important variables, states, or decisions within a
        method that are useful for developers to diagnose problems. It provides
        context for how a component is operating. This level is usually
        disabled in production but enabled during development and testing.

        Example:
            logger.debug(f"User ID {user.id} authenticated successfully.")
            logger.debug(f"Calculated execution plan with {len(plan.stages)} stages.")
        """
        self._log(LogType.DEBUG, message, encoding=encoding, separator=separator)

    def info(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        """
        Logs an INFO level message for tracking the normal flow of the application.

        Use this to report major lifecycle events, such as the start and end of
        a service, the completion of a significant task, or important configuration
        details at startup. These logs are intended for system administrators and
        developers to monitor the application's high-level behavior in production.

        Example:
            logger.info("Application startup complete.")
            logger.info(f"Starting dynamic batch of {total_tracks} tracks.")
        """
        self._log(LogType.INFO, message, encoding=encoding, separator=separator)

    def warning(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        """
        Logs a WARNING level message for unexpected but recoverable events.

        Use this to indicate a potential problem that does not prevent the current
        operation from completing but may require attention. This includes deprecated
        API usage, configuration issues, or non-critical errors that were handled.

        Example:
            logger.warning("Configuration value 'timeout' not set, using default of 30s.")
            logger.warning(f"Feature '{feature}' not found in results, skipping.")
        """
        self._log(LogType.WARNING, message, encoding=encoding, separator=separator)

    def error(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        """
        Logs an ERROR level message for failures that disrupt a single operation.

        Use this when a specific task or request fails but the overall application
        can continue running. This includes exceptions that are caught and handled,
        failed API calls, or invalid input that prevents a process from completing.
        These events require developer attention.

        Example:
            logger.error(f"Failed to process track {track_id}: {e}", exc_info=True)
            logger.error("Could not connect to the database after 3 retries.")
        """
        self._log(LogType.ERROR, message, encoding=encoding, separator=separator)

    def critical(
            self,
            message: str,
            force_show: bool = False,
            encoding: str = "utf-8",
            separator: str = None,
    ) -> None:
        """
        Logs a CRITICAL level message for severe failures that threaten the application.

        Use this for errors that are unrecoverable and may cause the entire
        application or service to shut down. This level indicates a catastrophic
        failure that requires immediate, urgent attention.

        Example:
            logger.critical("Failed to acquire database lock, application cannot start.")
            logger.critical("Out of memory error, shutting down worker process.")
        """
        self._log(LogType.CRITICAL, message, encoding=encoding, separator=separator)

    def get_outputs(self) -> List[HoornLogOutputInterface]:
        return self._outputs

    def log_raw(self, log_type: LogType, message: str, force_show: bool = False, encoding: str = "utf-8", separator: str = None) -> None:
        """Logs depending on the log-type.
        This is only provided for the specific case you want to log to a level based on configuration but don't want to manually switch-case.
        It is recommended to use the specific modes otherwise.
        """
        self._log(log_type, message, encoding=encoding, separator=separator)
