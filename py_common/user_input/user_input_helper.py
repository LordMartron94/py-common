import time
from typing import TypeVar, Type

from typing_extensions import Callable

from ..constants import CONSOLE_OUTPUT_LOCK
from ..logging import HoornLogger

T = TypeVar('T')


class UserInputHelper:
	"""
	This is a utility class to help get input from the user and validate it immediately.

    Very useful to combine with ``CommandLineInterface`` (:py:class:`cli_bench.common.py_common.cli_framework.CommandLineInterface`)
	"""

	def __init__(self, logger: HoornLogger, module_name: str = "UserInputHelper"):
		self._logger = logger
		self._module_name = module_name

	def get_user_input(self, prompt: str, expected_response_type: Type[T], validator_func: Callable[[T], [bool, str]], error_ignores_default: bool = True) -> T:
		"""Get user input and validate it immediately. Return the validated response.

		:param prompt: The prompt to display to the user.
		:param expected_response_type: The type of the expected response.
		:param validator_func: The function to validate the user input.
		:param error_ignores_default: Whether to ignore the error messages in the default logger output (console). Default is True.
		:return: The validated user input.
		"""

		with CONSOLE_OUTPUT_LOCK:
			print(prompt)
			user_input = input(">>> ")

		try:
			parsed = expected_response_type(user_input)
		except ValueError:
			self._logger.error("${ignore=default}" if error_ignores_default else "" + f"Invalid input '{user_input}'. Expected '{expected_response_type.__name__}'.", separator=self._module_name)
			with CONSOLE_OUTPUT_LOCK:
				print("Please try again. This is not a valid input: 'Unparsable input format.'")

			time.sleep(0.2)
			return self.get_user_input(prompt, expected_response_type, validator_func)

		validated, message = validator_func(parsed)

		if not validated:
			self._logger.error("${ignore=default}" if error_ignores_default else "" + f"Invalid input '{user_input}'.", separator=self._module_name)

			with CONSOLE_OUTPUT_LOCK:
				print(f"Please try again. This is not a valid input: '{message}'")
			time.sleep(0.2)
			return self.get_user_input(prompt, expected_response_type, validator_func)

		return parsed
