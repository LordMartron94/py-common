import json
from datetime import datetime
from msilib import gen_uuid
from pathlib import Path
from pprint import pprint
from typing import TextIO

from .logging import HoornLogger
from .networking.connector import Connector
from .networking.message_processor import MessageProcessor


class ComponentRegistration:
	"""
	Functions as the registration functionality to use libraries as a dedicated component
	(or set of components) in my Component-Based Architecture Foundation.
	Remember to call this in your script that gets run.
	"""

	def __init__(self, logger: HoornLogger, host: str = "127.0.0.1", port: int = 3333, component_port: int = 50001, module_separator = "Common", end_of_message_marker = "<eom>"):
		self._host = host
		self._port = port
		self._component_port = component_port

		self._logger: HoornLogger = logger

		self._message_processor: MessageProcessor = MessageProcessor(logger, shutdown_subscribers=[self._shutdown])

		self._connector: Connector = Connector(logger, end_of_message_token=end_of_message_marker, message_received_listener=self._message_processor.process_message)

		self._module_separator = module_separator
		self._end_of_message_marker = end_of_message_marker

	def _shutdown(self) -> None:
		self._connector.shutdown()

	def register_component(self, registration_json_path: Path, component_signature_json_path: Path):
		sock = self._connector.connect_to_remote(self._host, self._port, self._component_port)

		if sock is None:
			self._logger.error("Cannot register component because there is no socket available.", separator=self._module_separator)
			return

		with open(registration_json_path, 'r') as registration_file:
			message: bytes = self._encode_message(registration_file, component_signature_json_path)
			self._logger.debug("Registering Component to Middleman", separator=self._module_separator)
			sock.sendall(message)

	def register_logging(self) -> None:
		script_path: Path = Path(__file__).parent.joinpath('registration.json')
		component_signature_path: Path = Path(__file__).parent.joinpath('component_signature.json')
		self.register_component(script_path, component_signature_path)

	def _encode_message(self, registration_file: TextIO, component_registration_file: Path) -> bytes:
		message = json.load(registration_file)
		message["time_sent"] = str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z" )
		message["unique_id"] = gen_uuid()

		with open(component_registration_file, 'r') as f:
			json_string = json.loads(f.read())
			json_string = json.dumps(json_string)
			message["payload"]["args"].append({"type": "list", "value": json_string})

		message = json.dumps(message)
		message += self._end_of_message_marker
		byte_buffer = bytes(message, encoding='utf-8')
		return byte_buffer
