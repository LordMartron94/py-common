from pprint import pprint
from typing import Callable

from .connector import Connector
from .message_model import MessageModel
from ..logging import HoornLogger

class MessageProcessor:
	"""
	Processes server requests.
	"""
	def __init__(self, logger: HoornLogger, connector: Connector, module_separator = "Common.MessageProcessor"):
		self._module_separator: str = module_separator
		self._logger: HoornLogger = logger
		self._connector: Connector = connector

		self._message_handlers = {}

	def send_request(self, message: MessageModel, on_response_callback: Callable[[MessageModel], None]):
		self._message_handlers[message.unique_id] = on_response_callback
		self._connector.send_request(message)

	def process_message(self, msg: MessageModel) -> None:
		# pprint(self._message_handlers)

		self._logger.trace(f"Processing message: {msg.unique_id}", separator=self._module_separator)

		for unique_id, message_handler in self._message_handlers.items():
			if unique_id == msg.target_uuid:
				self._logger.trace(f"Found response handler for message: {message_handler}", separator=self._module_separator)
				message_handler(msg)
				del self._message_handlers[unique_id]
				return

		self._logger.warning(f"Received message from server with no associated request: {msg.model_dump()}", separator=self._module_separator)
