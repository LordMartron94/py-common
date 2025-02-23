import time
from typing import TypeVar, Callable

from ..logging import HoornLogger
from ..time_handling import TimeUtils
from ..time_handling.time_utils import time_operation

T = TypeVar('T')
U = TypeVar('U')


class Worker:
    """Represents a single worker thread."""

    def __init__(self,
                 logger: HoornLogger,
                 worker_id: str,
                 work_to_perform: Callable[[T, U], None],
                 return_to_pool_func: Callable[["Worker"], None],
                 time_utils: TimeUtils):
        self._worker_id = worker_id
        self._logger = logger
        self._work_func = work_to_perform
        self._return_to_pool = return_to_pool_func
        self._time_utils = time_utils
        self._logger.trace(f"Initialized successfully.", separator=self._worker_id)

    def get_worker_id(self) -> str:
        return self._worker_id

    def __work(self, data: T, context: U):
        @time_operation(logger=self._logger, time_utils=self._time_utils, separator=self._worker_id)
        def worker_wrapper():
            self._work_func(data, context)

        worker_wrapper()

    def work(self, data: T, context: U):
        """Performs an operation on the data and logs the elapsed time to the debug logs."""

        self._logger.trace(f"Started working.", separator=self._worker_id)
        self.__work(data, context)
        self._return_to_pool(self)
