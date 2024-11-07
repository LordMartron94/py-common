import json
import socket
import threading
import time
from typing import List, Callable

from .argument_model import ArgumentModel
from .message_payload import MessagePayload
from ..logging import HoornLogger


class Connector:
	"""
	Low-Level API for connecting with remote hosts.
	"""
	def __init__(self, logger: HoornLogger, message_received_listener: Callable[[MessagePayload], None], module_separator: str = "Common.Connector", end_of_message_token: str = "<eom>"):
		self._logger = logger
		self._message_received_listener: Callable[[MessagePayload], None] = message_received_listener

		self._module_separator = module_separator
		self._shutdown_signal: threading.Event = threading.Event()
		self._end_of_message_token = end_of_message_token

	def shutdown(self):
		self._logger.debug("Stopping listening loop because of shutdown signal.", separator=self._module_separator)
		time.sleep(1)
		self._shutdown_signal.set()

	def connect_to_remote(self, host: str, port: int, component_port: int = 5555) -> socket:
		"""Connects to a remote host and port using TCP and continuously listens for data.

		Args:
		   host: The hostname or IP address of the remote host.
		   port: The port number on the remote host.
		   component_port: The port number to bind the socket to. Defaults to 5555.

		Returns:
		   None. Logs error messages on failure.
		"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((host, component_port))
		try:
			s.connect((host, port))
		except ConnectionRefusedError:
			self._logger.error(f"Connection refused by {host}:{port}", separator=self._module_separator)
			return None
		self._logger.info(f"Connected to {host}:{port}", separator=self._module_separator)

		thread = threading.Thread(target=self.read_data_loop, args=(s, host, port, self._shutdown_signal))
		thread.start()

		return s

	def read_data_loop(self, s: socket, host: str, port: int, shutdown_signal: threading.Event):
		buffer = b""
		while not shutdown_signal.is_set():
			try:
				data = s.recv(4096)
				if not data:
					self._logger.info(f"Connection closed by {host}:{port}", separator=self._module_separator)
					break

				buffer += data

				if self._end_of_message_token.encode() in buffer:
					message, remaining = buffer.split(self._end_of_message_token.encode(), 1)
					message = message.decode()
					self._process_message(message, host, port)
					buffer = remaining

			except socket.timeout:
				self._logger.warning(f"Timeout while receiving data from {host}:{port}", separator=self._module_separator)
			except OSError as e:
				self._logger.error(f"Error receiving data from {host}:{port}: {e}", separator=self._module_separator)
				break

	def _process_message(self, data: str, host: str, port: int) -> None:
		self._logger.debug(f"Received from {host}:{port}: {data}", separator=self._module_separator)
		json_data = json.loads(data)

		message_payload = json_data["payload"]
		args: List[ArgumentModel] = []

		for arg_data in message_payload["args"]:
			args.append(ArgumentModel(
				type=arg_data["type"],
				value=arg_data["value"]
			))

		processed_message: MessagePayload = MessagePayload(
			action=message_payload["action"],
			args=args
		)

		self._message_received_listener(processed_message)
