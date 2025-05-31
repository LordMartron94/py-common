import pprint
from dataclasses import dataclass
from typing import Dict, List, Callable, Optional

import numpy as np

from ...logging import HoornLogger


@dataclass
class ScoreResult:
    matrix: np.ndarray
    labels: List[str]


class TemplateMatcher:
    """
    A generic matcher that computes similarity scores between feature vectors
    and a set of named templates, producing an (n_vectors x n_templates) score matrix.

    Can accept an optional preprocessing function to normalize or transform
    each feature vector before scoring.
    """
    def __init__(
            self,
            logger: HoornLogger,
            templates: Dict[str, np.ndarray],
            similarity_fn: Optional[Callable[[np.ndarray, np.ndarray], float]] = None,
            preprocessor: Optional[Callable[[np.ndarray], np.ndarray]] = None,
            label_order: Optional[List[str]] = None,
            verbose: bool = False,
    ):
        """
        :param logger: HoornLogger instance for logging
        :param templates: mapping from template name to template vector (assumed normalized)
        :param similarity_fn: function(vector, template) -> float; defaults to Pearson correlation
        :param preprocessor: function(vector) -> vector; applied before scoring
        :param label_order: explicit ordering of template names; defaults to dict insertion order
        """
        self._logger = logger
        self._separator = self.__class__.__name__
        self._templates = templates
        self._labels = label_order or list(templates.keys())
        self._similarity_fn = similarity_fn or self._pearson_correlation
        self._preprocessor = preprocessor or (lambda x: x)
        self._verbose = verbose

        self._logger.trace(
            f"Initialized TemplateMatcher with {len(self._labels)} templates.",
            separator=self._separator
        )

    @staticmethod
    def _pearson_correlation(v1: np.ndarray, v2: np.ndarray) -> float:
        corr = np.corrcoef(v1, v2)
        return float(corr[0, 1])

    def match(self, vectors: List[np.ndarray]) -> ScoreResult:
        """
        Compute the score matrix comparing each vector against each template.

        :param vectors: list of feature vectors
        :return: ScoreResult(matrix, labels)
        """
        self._logger.debug(
            f"Starting match on {len(vectors)} feature vectors.",
            separator=self._separator
        )

        num_vectors = len(vectors)
        num_templates = len(self._labels)
        score_matrix = np.zeros((num_vectors, num_templates), dtype=float)

        for i, vec in enumerate(vectors):
            self._logger.trace(
                f"Processing vector {i+1}/{num_vectors}.",
                separator=self._separator
            )
            try:
                processed = self._preprocessor(vec)
            except Exception as e:
                self._logger.error(
                    f"Preprocessing failed for vector {i}: {e}",
                    separator=self._separator
                )
                processed = vec

            for j, label in enumerate(self._labels):
                try:
                    template = self._templates[label]
                    score = self._similarity_fn(processed, template)
                    score_matrix[i, j] = score
                except Exception as e:
                    self._logger.warning(
                        f"Scoring failed for vector {i}, template '{label}': {e}",
                        separator=self._separator
                    )
                    score_matrix[i, j] = float('-inf')

            # Debug: log scores for the current vector across all templates
            scores_for_vector = {label: score_matrix[i, idx] for idx, label in enumerate(self._labels)}
            if self._verbose:
                self._logger.debug(
                    f"Scores for vector {i}\n{pprint.pformat(scores_for_vector)}",
                    separator=self._separator
                )

        self._logger.info(
            "Completed matching. Returning score matrix and labels.",
            separator=self._separator
        )

        result = ScoreResult(matrix=score_matrix, labels=self._labels)
        return result
