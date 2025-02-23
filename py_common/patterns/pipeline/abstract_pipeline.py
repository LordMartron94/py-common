from abc import ABC, abstractmethod
from typing import Any, List, Callable

from .pipe import IPipe

class ExitCheckPipe(IPipe):
    def __init__(self, exit_condition: Callable[[Any], bool], signal_exit_func: Callable):
        self._exit_condition = exit_condition
        self._signal_exit_func = signal_exit_func

    def flow(self, data: Any) -> Any:
        if self._exit_condition(data): self._signal_exit_func()


class AbPipeline(ABC):
    def __init__(self):
        self._pipes: List[IPipe] = []
        self._data: Any = None
        self._must_exit: bool = False

    def __exit_signal_func(self):
        self._must_exit = True

    def _add_step(self, step: IPipe):
        self._pipes.append(step)

    def _add_exit_check(self, check: Callable[[Any], bool]):
        self._add_step(ExitCheckPipe(check, self.__exit_signal_func))

    def flow(self, data: Any):
        """Makes the pipeline flow; run its steps/pipes."""
        self._data = data
        for pipe in self._pipes:
            self._data = pipe.flow(self._data)

            if self._must_exit:
                break

        return self._data

    @abstractmethod
    def build_pipeline(self):
        """
        Method to be implemented by subclasses.
        This method should populate the pipeline with steps using the add_step method.
        """
        pass
