from typing import List, Dict, Callable

from pandas import Series
from rapidfuzz import fuzz


def calculate_similarity_score(rows: List[Series], field_weights: Dict[str, float],
                               similarity_func: Callable[[str, str], float] = fuzz.token_sort_ratio) -> float:
    """
    Calculate a weighted similarity score between multiple rows based on specified fields and their weights.

    Args:
        rows (List[Series]): A list of rows containing the fields to compare.
        field_weights (Dict[str, float]): A dictionary where keys are field names and values are their weights.
        similarity_func (Callable): A function to calculate similarity between two strings (default: fuzz.token_sort_ratio).

    Returns:
        float: The weighted similarity score.
    """
    if len(rows) < 2:
        raise ValueError("At least two rows are required for similarity calculation.")

    # Aggregate similarity scores for each field
    composite_score = 0.0
    for field, weight in field_weights.items():
        # Calculate pairwise similarity and average across all combinations
        pair_scores = [
            similarity_func(str(row1[field]), str(row2[field]))
            for i, row1 in enumerate(rows)
            for j, row2 in enumerate(rows)
            if i < j  # Avoid redundant comparisons and self-comparisons
        ]
        average_score = sum(pair_scores) / len(pair_scores) if pair_scores else 0.0
        composite_score += weight * average_score

    return composite_score
