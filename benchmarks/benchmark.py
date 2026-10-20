"""Performance benchmark comparing Python baseline vs NumPy vectorization."""

import time

import numpy as np

from hotel_booking.analytics import (
    calculate_descriptive_statistics,
    calculate_vectorized_revenue,
)


def benchmark_statistics(dataset_size: int = 200_000) -> None:
    print(f"=== Running Statistics Benchmark (N={dataset_size:,}) ===")
    np.random.seed(42)
    prices = list(np.random.uniform(50.0, 500.0, size=dataset_size))

    # Python baseline
    start_py = time.perf_counter()
    mean_val = sum(prices) / len(prices)
    min_val = min(prices)
    max_val = max(prices)
    variance = sum((x - mean_val) ** 2 for x in prices) / len(prices)
    std_val = variance**0.5
    py_duration = time.perf_counter() - start_py

    # NumPy vectorized
    start_np = time.perf_counter()
    np_stats = calculate_descriptive_statistics(prices)
    np_duration = time.perf_counter() - start_np

    speedup = py_duration / np_duration if np_duration > 0 else float("inf")
    print(
        f"Python baseline:  {py_duration * 1000:.3f} ms "
        f"(mean={mean_val:.2f}, min={min_val:.2f}, max={max_val:.2f}, std={std_val:.2f})"
    )
    print(
        f"NumPy vectorized: {np_duration * 1000:.3f} ms "
        f"(mean={np_stats['mean']:.2f}, min={np_stats['min']:.2f}, "
        f"max={np_stats['max']:.2f}, std={np_stats['std']:.2f})"
    )
    print(f"Speedup factor:   {speedup:.2f}x\n")


def benchmark_revenue(dataset_size: int = 200_000) -> None:
    print(f"=== Running Revenue Dot Product Benchmark (N={dataset_size:,}) ===")
    np.random.seed(42)
    prices = list(np.random.uniform(80.0, 400.0, size=dataset_size))
    nights = list(np.random.randint(1, 14, size=dataset_size))

    # Python baseline
    start_py = time.perf_counter()
    total_py = sum(p * n for p, n in zip(prices, nights, strict=False))
    py_duration = time.perf_counter() - start_py

    # NumPy vectorized
    start_np = time.perf_counter()
    total_np = calculate_vectorized_revenue(prices, nights)
    np_duration = time.perf_counter() - start_np

    speedup = py_duration / np_duration if np_duration > 0 else float("inf")
    print(f"Python baseline:  {py_duration * 1000:.3f} ms (revenue={total_py:,.2f})")
    print(f"NumPy vectorized: {np_duration * 1000:.3f} ms (revenue={total_np:,.2f})")
    print(f"Speedup factor:   {speedup:.2f}x\n")


if __name__ == "__main__":
    benchmark_statistics()
    benchmark_revenue()
