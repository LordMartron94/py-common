import os
import subprocess
from pathlib import Path

from common.logging import HoornLogger


class CommandHelper:
	"""
	Helper class meant to streamline the execution of a command in command prompt. Enjoy.
	"""

	def __init__(self, hoorn_logger: HoornLogger, debug_mode: bool = False):
		self._logger: HoornLogger = hoorn_logger
		self._debug_mode: bool = debug_mode

	def _format_error(self, stderr: str) -> str:
		formatted = "Error executing command:\n"

		for line in stderr.split('\n'):
			formatted += f"  {line}\n"

		return formatted

	def execute_command(self, command: list, output_override: bool = False) -> subprocess.CompletedProcess:
		"""
		Executes a given command.
		Prints errors in all cases.
		"""
		if self._debug_mode or output_override:
			self._logger.info(f"Executing command: {command}")
			self._logger.info(f"Stringified: {' '.join(command)}")

		result = subprocess.run(command, capture_output=True)
		if result.returncode != 0:
			error_message = self._format_error(result.stderr.decode('utf-8'))
			self._logger.error(error_message)

			if not self._debug_mode:
				self._logger.info(f"Command causing error: {command}")

		return result

	def execute_command_v2(self, executable: Path, command: list):
		"""Use this if `execute_command` does not work."""

		if self._debug_mode:
			self._logger.info(f"Executing {' '.join(command)} with executable {executable}")

		bat_file_path = Path(__file__).parent.joinpath("temp.bat")

		with open(bat_file_path, 'w') as bat_file:
			bat_file.write(f'"{executable}" {" ".join(command)}\n')
			bat_file.write(f'exit\n')

		print(bat_file_path)
		subprocess.run(['start', os.environ["COMSPEC"], '/k', f"{bat_file_path}"], shell=True)

	def open_python_module_with_custom_interpreter(self, interpreter_path: Path, working_directory: Path, module_name: str, args: list[str]):
		"""
		Opens a python module with a custom interpreter.
		"""

		if self._debug_mode:
			self._logger.info(f"Opening module {module_name} with interpreter {interpreter_path}")

		bat_file_path = Path(__file__).parent.joinpath("temp.bat")

		with open(bat_file_path, 'w') as bat_file:
			bat_file.write(f'cd "{working_directory}"\n')
			bat_file.write(f'"{interpreter_path}" -m {module_name} {" ".join(args)}\n')
			bat_file.write(f'pause\n')

		print(bat_file_path)
		subprocess.run(['start', os.environ["COMSPEC"], '/k', f"{bat_file_path}"], shell=True)
