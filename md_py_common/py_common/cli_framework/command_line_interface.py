import time
from typing import List, Callable, Union

from .command_model import CommandModel
from ..logging import HoornLogger
from ..utils import ColorHelper


class CommandLineInterface:
	"""Module to allow for easy implementation of command line interfaces."""

	def __init__(self, logger: HoornLogger, command_prefix: str = "/", initialize_with_help_command: bool = True):
		self._logger = logger
		self._command_prefix: str = command_prefix
		self._commands: List[CommandModel] = []
		self._color_helper: ColorHelper = ColorHelper()

		if initialize_with_help_command:
			self.add_command(["help", "?"], "Displays this help message.", self.print_help)

		self._logger.debug("Successfully initialized CommandLineInterface")

	def _command_exists(self, keys: List[str]) -> bool:
		for command in self._commands:
			for command_key in command.commands:
				if command_key in keys:
					return True

		return False

	def add_command(self, keys: List[str], description: str, action: Callable) -> None:
		"""
		Add a new command to the command line interface.

		:param keys: The keys (aliases) for the command.
		WITHOUT the prefix.
		:param description: A brief description of the command.
		:param action: The function to execute when the command is called.

		Does nothing if the command already exists.
		If you want to update an existing command, use the update_command method instead.
		"""

		if self._command_exists(keys):
			self._logger.warning(f"Command with keys {keys} already exists. Skipping.")
			return

		command_model = CommandModel(commands=[f"{self._command_prefix}{key}" for key in keys], description=description, action=action)
		self._commands.append(command_model)

	def update_command(self, keys: List[str], description: str, action: Callable) -> None:
		"""
		Update an existing command in the command line interface.

        :param keys: The keys (aliases) for the command.
        :param description: A brief description of the command.
        :param action: The function to execute when the command is called.

        Does nothing if the command does not exist.
        """

		if not self._command_exists(keys):
			self._logger.warning(f"Command with keys {keys} does not exist. Skipping.")
			return

		for command in self._commands:
			if command.commands == keys:
				command.description = description
				command.action = action
				return

	def add_alias_to_command(self, original_aliases: List[str], added_alias: str) -> None:
		"""
        Add an alias to an existing command.

        :param original_aliases: The original keys (aliases) for the command.
        :param added_alias: The alias to add.

        Does nothing if the original command does not exist.
        """

		if not self._command_exists(original_aliases):
			self._logger.warning(f"Command with keys {original_aliases} does not exist. Skipping.")
			return

		for command in self._commands:
			if command.commands == original_aliases:
				command.keys.append(added_alias)
				return

	def start_listen_loop(self):
		while True:
			self._get_user_command()

	def _get_user_command(self):
		user_command: str = input(self._color_helper.colorize_string(">>> ", "#f3ce00"))
		if user_command.startswith(self._command_prefix):
			command: Union[CommandModel, None] = self._find_command_by_key(user_command)

			if command is None:
				self._logger.error(f"Command '{user_command}' not found. Please try again.")
				time.sleep(0.1)
				return self._get_user_command()

			command.action()
			return

		self._logger.error(f"Invalid command '{user_command}'. Please start with '{self._command_prefix}'.")

	def get_commands(self) -> List[CommandModel]:
		"""
        Get all the commands in the command line interface.

        :return: A list of CommandModel objects.
        """

		return self._commands

	def print_help(self, print_to_logger_also: bool = False) -> None:
		"""
        Print the help message for all the commands in the command line interface.
        """

		for command in self._commands:
			text: str = self._get_formatted_help_message(command.commands, command.description)

			if print_to_logger_also:
				self._logger.info(text)

			print(text)

	def _find_command_by_key(self, key: str) -> Union[CommandModel, None]:
		for command in self._commands:
			if key in command.commands:
				return command

		return None

	def _get_formatted_help_message(self, keys: List[str], description: str) -> str:
		keys_string = self._color_helper.colorize_string(f"| {', '.join(keys)} |", "#2196F3")
		description_string = self._color_helper.colorize_string(f"{description} |", "#795548")
		return f"{keys_string} {description_string}"
