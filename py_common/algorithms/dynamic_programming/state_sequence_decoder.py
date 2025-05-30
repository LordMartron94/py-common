import numpy as np
from typing import Tuple, Optional

from ...logging import HoornLogger


class StateSequenceDecoder:
    """
    A generic decoder using dynamic programming (Viterbi-style) to select the best sequence of states
    given per-segment scores and a fixed penalty for switching states.
    """

    def __init__(
            self,
            logger: HoornLogger,
            switching_penalty: Optional[float] = None
    ):
        """
        :param switching_penalty: cost to switch from one state to another. Defaults to 0.
        """
        self._logger = logger
        self._separator = self.__class__.__name__
        self._switching_penalty = switching_penalty or 0.0

        self._logger.trace(
            f"Initialized with switching_penalty={self._switching_penalty}",
            separator=self._separator
        )

    def decode(
            self,
            score_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Decode the optimal sequence of state indices for the given score matrix.

        :param score_matrix: a two-dimensional array with dimensions
                             (number_of_segments, number_of_states)
        :return: a one-dimensional array of length number_of_segments
                 containing the chosen state index for each segment
        """
        self._logger.debug(
            f"Decoding sequence for score_matrix of shape {score_matrix.shape}",
            separator=self._separator
        )
        dp_table, backpointer_table = self._initialize_tables(score_matrix)
        dp_table, backpointer_table = self._populate_tables(
            dp_table,
            backpointer_table,
            score_matrix
        )
        sequence = self._reconstruct_sequence(dp_table, backpointer_table)

        return sequence

    def _initialize_tables(
            self,
            score_matrix: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Initialize the dynamic programming table and backpointer table.
        The first row of the dynamic programming table is initialized
        to the first row of the score matrix.
        """
        self._logger.debug(
            "Initializing DP and backpointer tables", separator=self._separator
        )
        number_of_segments, number_of_states = score_matrix.shape
        dp_table = np.full(
            (number_of_segments, number_of_states),
            -np.inf
        )
        backpointer_table = np.zeros(
            (number_of_segments, number_of_states),
            dtype=int
        )
        dp_table[0] = score_matrix[0]
        self._logger.trace(
            f"First row set to scores: {dp_table[0]}",
            separator=self._separator
        )
        return dp_table, backpointer_table

    def _populate_tables(
            self,
            dp_table: np.ndarray,
            backpointer_table: np.ndarray,
            score_matrix: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fill the dynamic programming table using the recurrence.
        """
        self._logger.debug(
            "Populating DP and backpointer tables", separator=self._separator
        )
        number_of_segments, number_of_states = score_matrix.shape
        for segment in range(1, number_of_segments):
            previous_row = dp_table[segment - 1]
            highest_switch_score = np.max(
                previous_row - self._switching_penalty
            )
            index_of_highest_switch = int(np.argmax(
                previous_row - self._switching_penalty
            ))
            self._logger.trace(
                f"Segment {segment}: highest_switch_score={highest_switch_score}, "
                f"from_state={index_of_highest_switch}",
                separator=self._separator
            )
            for state in range(number_of_states):
                stay_score = previous_row[state]
                if stay_score >= highest_switch_score:
                    dp_table[segment, state] = (
                            score_matrix[segment, state] + stay_score
                    )
                    backpointer_table[segment, state] = state
                else:
                    dp_table[segment, state] = (
                            score_matrix[segment, state] + highest_switch_score
                    )
                    backpointer_table[segment, state] = index_of_highest_switch
                self._logger.trace(
                    f"dp[{segment},{state}]={dp_table[segment, state]}, "
                    f"bp={backpointer_table[segment, state]}",
                    separator=self._separator
                )
        self._logger.info(
            "Completed population of DP tables", separator=self._separator
        )
        return dp_table, backpointer_table

    def _reconstruct_sequence(
            self,
            dp_table: np.ndarray,
            backpointer_table: np.ndarray
    ) -> np.ndarray:
        """
        Reconstruct the optimal sequence of state indices by following backpointers
        from the last segment to the first.
        """
        self._logger.debug(
            "Reconstructing optimal sequence from DP tables", separator=self._separator
        )
        number_of_segments, _ = dp_table.shape
        optimal_sequence = np.zeros(number_of_segments, dtype=int)
        optimal_sequence[-1] = int(np.argmax(dp_table[-1]))
        self._logger.trace(
            f"Starting reconstruction at state {optimal_sequence[-1]} for last segment",
            separator=self._separator
        )
        for segment in range(number_of_segments - 2, -1, -1):
            next_state = optimal_sequence[segment + 1]
            optimal_sequence[segment] = backpointer_table[segment + 1, next_state]
            self._logger.trace(
                f"Reconstructed state for segment {segment}: {optimal_sequence[segment]}",
                separator=self._separator
            )
        self._logger.debug(
            f"Final reconstructed sequence: {optimal_sequence}", separator=self._separator
        )
        return optimal_sequence
