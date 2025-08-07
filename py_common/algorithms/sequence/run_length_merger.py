from dataclasses import dataclass
from typing import List, Tuple, Any

from ...logging import HoornLogger


@dataclass(frozen=True)
class StateRun:
    """
    Represents a contiguous run of a single state.
    """
    start_time: float
    end_time: float
    state_label: str
    start_index: int


class RunLengthMerger:
    """
    Collapses a sequence of state indices and their time spans into
    contiguous runs of identical states.
    """
    def __init__(
            self,
            logger: HoornLogger
    ):
        """
        :param logger: HoornLogger instance for logging
        """
        self._logger = logger
        self._separator = self.__class__.__name__
        self._logger.trace(
            "Initialized RunLengthMerger.",
            separator=self._separator
        )

    def merge(
            self,
            times: List[Tuple[float, float]],
            states: List[int],
            labels: List[str]
    ) -> List[StateRun]:
        """
        Merge segments into runs where consecutive state indices match.

        :param times: list of (start_time, end_time) per segment
        :param states: list of state indices per segment
        :param labels: list of state labels corresponding to indices
        :return: list of StateRun dataclasses
        """
        self._log_start(len(states))
        if not states:
            self._logger.warning(
                "Empty state sequence; no runs to merge.",
                separator=self._separator
            )
            return []

        runs = self._build_runs(times, states, labels)
        self._log_completion(len(runs))
        return runs

    def _build_runs(
            self,
            times: List[Tuple[float, float]],
            states: List[int],
            labels: List[str]
    ) -> List[StateRun]:
        """
        Core logic: iterate once through states and times to build StateRun instances.
        """
        runs: List[StateRun] = []
        run_start = 0
        current_state = states[0]

        for idx in range(1, len(states)):
            if states[idx] != current_state:
                runs.append(self._create_run(run_start, idx-1, times, current_state, labels))
                run_start = idx
                current_state = states[idx]

        # append last run
        runs.append(self._create_run(run_start, len(states)-1, times, current_state, labels))
        return runs

    def _create_run(
            self,
            start_idx: int,
            end_idx: int,
            times: List[Tuple[float, float]],
            state_idx: int,
            labels: List[str]
    ) -> StateRun:
        """
        Helper to build a StateRun from indices.
        """
        start_time, _ = times[start_idx]
        _, end_time = times[end_idx]
        state_label = labels[state_idx]
        run = StateRun(
            start_time=start_time,
            end_time=end_time,
            state_label=state_label,
            start_index=start_idx
        )
        self._logger.trace(
            f"Created run: {run}",
            separator=self._separator
        )
        return run

    def _log_start(self, segment_count: int) -> None:
        self._logger.debug(
            f"Merging {segment_count} segments into runs.",
            separator=self._separator
        )

    def _log_completion(self, run_count: int) -> None:
        self._logger.info(
            f"Merging complete: {run_count} runs generated.",
            separator=self._separator
        )
