import time
from typing import TypeVar, Callable

from ..logging import HoornLogger
from ..time_handling import TimeUtils

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
        self._work = work_to_perform
        self._return_to_pool = return_to_pool_func
        self._time_utils = time_utils
        self._logger.trace(f"Initialized successfully.", separator=self._worker_id)

    def get_worker_id(self) -> str:
        return self._worker_id

    def work(self, data: T, context: U):
        """Performs an operation on the data and logs the elapsed time to the trace logs."""

        self._logger.trace(f"Started working.", separator=self._worker_id)
        start_time = time.time()
        self._work(data, context)
        end_time = time.time()
        elapsed = end_time - start_time
        self._logger.trace(f"Finished working. Elapsed time: {self._time_utils.format_time(elapsed)}.", separator=self._worker_id)
        self._return_to_pool(self)
