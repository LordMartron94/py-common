import math


def lerp(start, end, t) -> float:
    """Linear interpolation function"""
    return (1 - t) * start + t * end

def gaussian_exponential_kernel(distance: float, sigma: float) -> float:
    """Computes a confidence factor based on the distance between X and Y and a sigma heuristic.
    Uses a gaussian exponential kernel.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")

    squared_distance: float = math.pow(distance, 2)
    computed_heuristic = (math.pow(sigma, 2) * 2)

    similarity: float = math.exp(-(squared_distance / computed_heuristic))
    similarity = similarity * 100
    similarity = max(0.0, min(similarity, 100.0))
    return similarity
