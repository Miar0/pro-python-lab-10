"""Performance analytics module: NumPy vectorization and LRU caching (from Lab 9)."""

from functools import lru_cache

import numpy as np


def calculate_descriptive_statistics(prices: list[float]) -> dict[str, float]:
    """Calculate mean, min, max, and std of prices using vectorized NumPy operations."""
    if not prices:
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "count": 0.0}

    arr = np.asarray(prices, dtype=np.float64)
    return {
        "mean": float(np.mean(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "std": float(np.std(arr)),
        "count": float(len(arr)),
    }


def calculate_vectorized_revenue(prices: list[float], nights: list[int]) -> float:
    """Calculate total hotel revenue via vectorized dot product of prices and nights."""
    if not prices or not nights or len(prices) != len(nights):
        return 0.0

    prices_arr = np.asarray(prices, dtype=np.float64)
    nights_arr = np.asarray(nights, dtype=np.float64)
    total = np.dot(prices_arr, nights_arr)
    return float(total)


class CachedHotelAnalytics:
    """Analytics helper with LRU caching and cache invalidation support."""

    def __init__(self) -> None:
        self.version: int = 1

    def invalidate(self) -> None:
        """Bump version and clear cache on data mutation."""
        self.version += 1
        self._cached_summary.cache_clear()

    def get_summary(self, prices: tuple[float, ...]) -> dict[str, float]:
        """Fetch descriptive statistics using cached calculations."""
        return self._cached_summary(prices, self.version)

    @staticmethod
    @lru_cache(maxsize=128)
    def _cached_summary(prices: tuple[float, ...], version: int) -> dict[str, float]:
        return calculate_descriptive_statistics(list(prices))
