import functools
import time

from decorator import decorator

from .time_format import TimeFormat
from .time_formatter_factory import TimeFormatterFactory
from .time_formatters.time_formatter import ABCTimeFormatter
from ..logging import HoornLogger


class TimeUtils:
	"""
	A utility class for formatting time.
	"""

	def __init__(self):
		self._formatter_factory: TimeFormatterFactory = TimeFormatterFactory()

	def format_time(self, total_seconds: float, time_format: TimeFormat=TimeFormat.HMS, round_digits=4) -> str:
		"""
		Formats the given total seconds into hours, minutes, and seconds based on the selected format.

		Args:
			total_seconds (int): The total number of seconds.
			time_format (TimeFormat): The format type to use. Default is TimeFormat.HMS.
			round_digits (int): The amount of digits to round seconds to. Defaults to 4.

		Returns:
			str: A string representing the formatted time.

		Raises:
			ValueError: If the specified format type is invalid.
		"""
		if time_format == TimeFormat.Dynamic:
			return self._format_dynamic(total_seconds, round_digits)

		formatter: ABCTimeFormatter = self._formatter_factory.create_time_formatter(time_format)
		return formatter.format(total_seconds, round_digits)


	def _format_dynamic(self, total_seconds: float, round_digits: int) -> str:
		if total_seconds >= 3600:
			return self._formatter_factory.create_time_formatter(TimeFormat.HMS).format(total_seconds, round_digits)
		if total_seconds >= 60:
			return self._formatter_factory.create_time_formatter(TimeFormat.MS).format(total_seconds, round_digits)
		return self._formatter_factory.create_time_formatter(TimeFormat.S).format(total_seconds, round_digits)

def time_operation(logger: HoornLogger, time_utils: TimeUtils, separator: str):
	"""
	A decorator for timing the execution of a function.

    Args:
        logger (HoornLogger): The logger to use for logging.
        time_utils (TimeUtils): The time utility to use for formatting time.
        separator (str): The separator to use for logging.

    Returns:
        function: The decorated function.
    """

	def decorator_time_operation(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			start_time = time.time()
			result = func(*args, **kwargs)
			end_time = time.time()
			elapsed = end_time - start_time
			logger.debug(f"Time taken by {func.__name__}: {time_utils.format_time(elapsed)}", separator=separator)
			return result
		return wrapper
	return decorator_time_operation
