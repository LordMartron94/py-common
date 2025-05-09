from typing import List, Dict, Callable, Optional
from pandas import Series
from rapidfuzz import fuzz


def calculate_similarity_score(
        rows: List[Series],
        field_weights: Dict[str, float],
        similarity_func: Callable[[str, str], float]=fuzz.token_sort_ratio,
        threshold: Optional[float] = None
) -> float:
    """
    Outward-facing API: delegates to specialized implementations based on number of rows.
    Supports an optional threshold cut-off to short-circuit early when it's impossible
    to exceed the given threshold.
    """
    if len(rows) == 2:
        return _score_two_rows(rows[0], rows[1], field_weights, similarity_func, threshold)
    return _score_multi_rows(rows, field_weights, similarity_func, threshold)


def _score_two_rows(
        row1: Series,
        row2: Series,
        field_weights: Dict[str, float],
        similarity_func: Callable[[str, str], float],
        threshold: Optional[float]
) -> float:
    """
    Optimized path for exactly two rows: avoids loops and list allocations.
    If threshold is provided, fields are scored in descending-weight order and we
    stop early when the maximum possible remaining score cannot reach threshold.
    """
    sim = similarity_func
    # Sort fields by descending weight to maximize early cutoff potential
    fields = sorted(field_weights.items(), key=lambda kv: kv[1], reverse=True)
    total = 0.0
    # Pre-extract string values
    values1 = {f: str(row1[f]) for f, _ in fields}
    values2 = {f: str(row2[f]) for f, _ in fields}
    # Remaining potential in raw score units (max 100 per weight unit)
    remaining_weight = sum(w for _, w in fields)

    for field, weight in fields:
        remaining_weight -= weight
        a = values1[field]
        b = values2[field]
        total += weight * sim(a, b)
        if threshold is not None and total + remaining_weight * 100 < threshold:
            break
    return total


def _score_multi_rows(
        rows: List[Series],
        field_weights: Dict[str, float],
        similarity_func: Callable[[str, str], float],
        threshold: Optional[float]
) -> float:
    """
    General path for N > 2 rows: minimizes Python overhead and supports
    optional threshold-based short-circuiting.
    """
    sim = similarity_func
    # Sort fields by descending weight for best early-exit potential
    fields = sorted(field_weights.items(), key=lambda kv: kv[1], reverse=True)
    n = len(rows)
    num_pairs = n * (n - 1) / 2
    composite = 0.0

    # Pre-extract strings per field per row
    extracted: Dict[str, List[str]] = {
        field: [str(r[field]) for r in rows]
        for field, _ in fields
    }
    # Remaining weight sum for potential (in weight units)
    remaining_weight = sum(w for _, w in fields)

    for field, weight in fields:
        remaining_weight -= weight
        texts = extracted[field]
        # accumulate similarity across all unique pairs
        subtotal = 0.0
        for i in range(n - 1):
            ai = texts[i]
            for j in range(i + 1, n):
                subtotal += sim(ai, texts[j])
        average = subtotal / num_pairs if num_pairs else 0.0
        composite += weight * average
        # Short-circuit: if threshold is set and even perfect remaining can't reach
        if threshold is not None and composite + remaining_weight * 100 < threshold:
            break

    return composite
