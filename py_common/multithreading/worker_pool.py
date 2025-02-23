import threading
from typing import Callable, List, Union

from .worker import Worker, T, U
from ..logging import HoornLogger


class WorkerPool:
    """Used to manage a pool of workers."""
    def __init__(self,
                 logger: HoornLogger,
                 pool_size: int,
                 work_template: Callable[[T, U], None],
                 worker_name: str,
                 grow_pool_automatically: bool=False,
                 grow_by: int=5):
        self._pool_lock = threading.Lock()

        self._separator = "Common.WorkerPool"
        self._logger = logger
        self._initial_pool_size = pool_size

        self._grow_pool_automatically = grow_pool_automatically
        self._grow_by = grow_by

        self._worker_template = work_template
        self._worker_name = worker_name

        self._last_worker_id: int = -1

        self._pool: List[Worker] = []
        self._initialize_pool()

        self._logger.trace("Successfully initialized.", separator=self._separator)

    def _initialize_pool(self):
        self._increase_num_workers(self._initial_pool_size)

    def _increase_num_workers(self, n: int):
        for _ in range(n):
            self._logger.debug(f"Creating worker '{self._worker_name}-{self._last_worker_id+1}'", separator=self._separator)
            self.__append_to_pool(self._generate_worker())

    def _return_to_pool(self, worker: Worker):
        self.__append_to_pool(worker)
        self._logger.debug(f"Returning worker '{worker.get_worker_id()}' to pool", separator=self._separator)

    def _generate_worker(self) -> Worker:
        self._last_worker_id += 1
        return Worker(self._logger, f"{self._worker_name}-{self._last_worker_id}", self._worker_template, self._return_to_pool)

    def __append_to_pool(self, worker: Worker):
        self._pool_lock.acquire()
        self._pool.append(worker)
        self._pool_lock.release()

    def __handle_empty_pool(self) -> Union[Worker, None]:
        if len(self._pool) <= 0:
            if not self._grow_pool_automatically:
                self._logger.warning("All workers are busy, try again later.", separator=self._separator)
                return None
            else:
                self._logger.debug("All workers are busy, but we can grow the pool.", separator=self._separator)
                self._increase_num_workers(self._grow_by)
                if len(self._pool) <=0:
                    return None
        worker = self._pool.pop(0)
        return worker

    def get_worker(self) -> Union[Worker, None]:
        # Uses double checks to reduce lock contention and improve performance.

        if len(self._pool) <= 0:
            self._pool_lock.acquire()
            try:
                return self.__handle_empty_pool()
            finally:
                self._pool_lock.release()
        else:
            self._pool_lock.acquire()
            try:
                worker = self._pool.pop(0)
                return worker
            finally:
                self._pool_lock.release()
