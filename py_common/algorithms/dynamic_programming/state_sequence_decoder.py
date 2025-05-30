import numpy as np
from typing import Tuple, Optional

from ...logging import HoornLogger


class StateSequenceDecoder:
    """
    A generic decoder using dynamic programming (Viterbi-style) to select the best sequence of states
    given per-segment scores and either a fixed penalty or a full penalty matrix for state transitions.
    """
    def __init__(
            self,
            logger: HoornLogger,
            switching_penalty: Optional[float] = None,
            penalty_matrix: Optional[np.ndarray] = None
    ):
        """
        :param switching_penalty: scalar cost to switch from any state to any other state
        :param penalty_matrix: a (n_states x n_states) array where entry [i,j]
                               is the cost to transition from state i to state j.
                               Overrides switching_penalty if provided.
        """
        self._logger = logger
        self._separator = self.__class__.__name__
        if penalty_matrix is not None:
            self._penalty_matrix = penalty_matrix
            self._logger.debug(
                f"Initialized with custom penalty matrix of shape {penalty_matrix.shape}.",
                separator=self._separator
            )
        else:
            self._switching_penalty = switching_penalty or 0.0
            self._penalty_matrix = None
            self._logger.debug(
                f"Initialized with uniform switching_penalty={self._switching_penalty}.",
                separator=self._separator
            )

    def decode(
            self,
            score_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Decode the optimal sequence of state indices for the given score_matrix.

        :param score_matrix: shape (n_segments, n_states)
        :return: array of length n_segments with chosen state index per segment
        """
        self._logger.info(
            f"Decoding sequence for score_matrix of shape {score_matrix.shape}",
            separator=self._separator
        )
        dp, backptr = self._initialize_tables(score_matrix)
        dp, backptr = self._populate_tables(dp, backptr, score_matrix)
        sequence = self._reconstruct_sequence(dp, backptr)
        self._logger.info(
            "Decoding complete.", separator=self._separator
        )
        return sequence

    def _initialize_tables(
            self,
            score_matrix: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        n_segments, n_states = score_matrix.shape
        dp = np.full((n_segments, n_states), -np.inf)
        backptr = np.zeros((n_segments, n_states), dtype=int)
        dp[0, :] = score_matrix[0, :]
        self._logger.trace(
            f"DP table initialized; first row set to {dp[0]}",
            separator=self._separator
        )
        return dp, backptr

    def _populate_tables(
            self,
            dp: np.ndarray,
            backptr: np.ndarray,
            score_matrix: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        n_segments, n_states = score_matrix.shape
        for t in range(1, n_segments):
            prev_row = dp[t - 1]
            for j in range(n_states):
                # compute best previous state
                if self._penalty_matrix is not None:
                    # vector of prev_row[k] - penalty_matrix[k,j]
                    costs = prev_row - self._penalty_matrix[:, j]
                else:
                    costs = prev_row - self._switching_penalty
                best_prev = int(np.argmax(costs))
                best_score = costs[best_prev]
                dp[t, j] = score_matrix[t, j] + best_score
                backptr[t, j] = best_prev
                self._logger.trace(
                    f"t={t}, state={j}: prev={best_prev}, score={dp[t,j]:.3f}",
                    separator=self._separator
                )
        return dp, backptr

    def _reconstruct_sequence(
            self,
            dp: np.ndarray,
            backptr: np.ndarray
    ) -> np.ndarray:
        n_segments, _ = dp.shape
        seq = np.zeros(n_segments, dtype=int)
        seq[-1] = int(np.argmax(dp[-1, :]))
        self._logger.trace(
            f"Starting backtrace at state={seq[-1]}", separator=self._separator
        )
        for t in range(n_segments - 2, -1, -1):
            seq[t] = backptr[t + 1, seq[t + 1]]
            self._logger.trace(
                f"Backtraced state for t={t}: {seq[t]}", separator=self._separator
            )
        return seq
