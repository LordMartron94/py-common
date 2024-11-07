from typing import List, Callable

from .message_payload import MessagePayload
from ..logging import HoornLogger


class MessageProcessor:
	"""
	Processes server requests.
	"""
	def __init__(self, logger: HoornLogger, module_separator = "Common.MessageProcessor", shutdown_subscribers: List[Callable[[], None]]=None):
		if shutdown_subscribers is None:
			shutdown_subscribers = []

		self._shutdown_subscribers: List[Callable[[], None]] = shutdown_subscribers
		self._module_separator: str = module_separator
		self._logger: HoornLogger = logger

	def add_shutdown_subscriber(self, subscriber: Callable[[], None]):
		if subscriber in self._shutdown_subscribers:
			self._logger.warning(f"Duplicate shutdown subscriber: {subscriber}", separator=self._module_separator)
			return

		self._shutdown_subscribers.append(subscriber)

	def process_message(self, payload: MessagePayload):
		# TODO - Convert into strategy pattern
		if payload.action == "response":
			self._logger.info(f"Received response: '{payload.args[0].value}' - code '{payload.args[1].value}'", separator=self._module_separator)
		elif payload.action == "shutdown":
			self._logger.info(f"Received shutdown request", separator=self._module_separator)
			for sub in self._shutdown_subscribers:
				sub()
		elif payload.action.startswith("log"):
			log_type = payload.action.split("log_")[1]
			self._logger.info(f"Received log '{log_type}': '{payload.args[0].value}'", separator=self._module_separator)

			if log_type == "debug":
				self._logger.debug(payload.args[0].value, bool(payload.args[1].value), payload.args[2].value if payload.args[2].value != "" else "utf-8", payload.args[3].value)
			elif log_type == "info":
				self._logger.info(payload.args[0].value, bool(payload.args[1].value), payload.args[2].value if payload.args[2].value != "" else "utf-8", payload.args[3].value)
			elif log_type == "warn":
				self._logger.warning(payload.args[0].value, bool(payload.args[1].value), payload.args[2].value if payload.args[2].value != "" else "utf-8", payload.args[3].value)
			elif log_type == "error":
				self._logger.error(payload.args[0].value, bool(payload.args[1].value), payload.args[2].value if payload.args[2].value != "" else "utf-8", payload.args[3].value)
			elif log_type == "critical":
				self._logger.critical(payload.args[0].value, bool(payload.args[1].value), payload.args[2].value if payload.args[2].value != "" else "utf-8", payload.args[3].value)
		else:
			self._logger.warning(f"Unknown request: {payload.action}", separator=self._module_separator)
