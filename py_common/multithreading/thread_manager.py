import threading
import time
from threading import Semaphore, Thread
from typing import Callable, List, Union

import pydantic

from .worker import T, Worker, U
from .worker_pool import WorkerPool
from ..logging import HoornLogger


class ThreadManagerConfig(pydantic.BaseModel):
    num_threads: int
    worker_template: Callable[[T], None]
    worker_name: str


class ThreadManager:
    """Used to divide work across multiple threads and in batches. Can severely increase performance/speed."""
    def __init__(self, logger: HoornLogger, config: ThreadManagerConfig):
        self._separator = "Common.ThreadManager"
        self._num_processed_batches: int = 0

        self._config: ThreadManagerConfig = config
        self._logger: HoornLogger = logger

        self._worker_pool: WorkerPool = WorkerPool(logger, self._config.num_threads, self._config.worker_template, self._config.worker_name)

        self._progress_lock: threading.Lock = threading.Lock()

        self._semaphore: Semaphore = Semaphore(self._config.num_threads)
        self._logger.trace("Successfully initialized.", separator=self._separator)

    def __get_worker(self, seconds_to_retry: float = 1) -> Worker:
        worker: Union[Worker, None] = self._worker_pool.get_worker()
        if worker:
            return worker
        else:
            self._logger.warning(f"No worker available, trying again in {seconds_to_retry} seconds...")
            time.sleep(seconds_to_retry)
            return self.__get_worker(seconds_to_retry * 1.5)

    def _work_batch(self, batch: T, worker_context: U, total_to_process: int):
        """Work on a batch of tasks."""
        try:
            self._semaphore.acquire()
            self._logger.trace(f"Working on batch: {batch}", separator=self._separator)
            worker: Worker = self.__get_worker()

            worker.work(batch, worker_context)

            with self._progress_lock:
                self._num_processed_batches += 1
                self._logger.info(
                    f"Processed {self._num_processed_batches}/{total_to_process} ({round(self._num_processed_batches / total_to_process * 100, 4)}%) batches.",
                    separator=self._separator
                )
        finally:
            self._semaphore.release()


    def work_batches(self, batches: List[T], worker_context: U) -> None:
        """
        Works on a set of batches.

        :param batches: The batches to work on.
        :param worker_context: The context for the batches.
        It is advised to make this context thread-safe.
        :return: None.
        """

        threads: List[Thread] = []
        self._logger.trace("Starting threads...", separator=self._separator)

        self._num_processed_batches = 0  # Reset the number of processed batches.
        total_to_process: int = len(batches)

        for batch in batches:
            thread = threading.Thread(target=self._work_batch, args=(batch, worker_context, total_to_process,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish executing.
        for thread in threads:
            thread.join()

        self._logger.info(f"Finished processing {total_to_process} batches.", separator=self._separator)
