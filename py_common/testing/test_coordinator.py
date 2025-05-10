from typing import List

import pydantic

from . import TestInterface
from ..cli_framework import CommandLineInterface
from ..constants import COMMON_LOGGING_PREFIX
from ..logging import HoornLogger


class TestConfiguration(pydantic.BaseModel):
    associated_test: TestInterface
    command_keys: List[str]
    command_description: str
    keyword_arguments: List

    model_config = {
        "arbitrary_types_allowed": True
    }


class TestCoordinator:
    """Used to coordinate between tests using the CLI framework."""
    def __init__(self, logger: HoornLogger, tests: List[TestConfiguration]):
        self._logger: HoornLogger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.TestCoordinator"

        self._cli_framework: CommandLineInterface = CommandLineInterface(
            logger,
            exit_command=self._exit_cli_loop
        )

        for test in tests:
            self._cli_framework.add_command(
                keys=test.command_keys,
                description=test.command_description,
                arguments=test.keyword_arguments,
                action=test.associated_test.test
            )

        self._logger.trace("Successfully initialized.", separator=self._separator)

    def _exit_cli_loop(self):
        self._cli_framework.exit_conversation_loop()

    def start_test_cli(self):
        self._cli_framework.start_listen_loop()
