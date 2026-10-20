"""Tests for analytics, NumPy vectorization, and LRU cache invalidation."""

from hotel_booking.analytics import (
    CachedHotelAnalytics,
    calculate_descriptive_statistics,
    calculate_vectorized_revenue,
)


def test_calculate_descriptive_statistics_empty() -> None:
    res = calculate_descriptive_statistics([])
    assert res["count"] == 0.0
    assert res["mean"] == 0.0


def test_calculate_descriptive_statistics_values() -> None:
    prices = [100.0, 200.0, 300.0]
    res = calculate_descriptive_statistics(prices)
    assert res["count"] == 3.0
    assert res["mean"] == 200.0
    assert res["min"] == 100.0
    assert res["max"] == 300.0
    assert res["std"] > 0.0


def test_calculate_vectorized_revenue() -> None:
    prices = [100.0, 150.0, 200.0]
    nights = [2, 3, 1]  # 200 + 450 + 200 = 850
    total = calculate_vectorized_revenue(prices, nights)
    assert total == 850.0

    assert calculate_vectorized_revenue([], []) == 0.0
    assert calculate_vectorized_revenue([100.0], [1, 2]) == 0.0


def test_cached_hotel_analytics_lifecycle() -> None:
    analytics = CachedHotelAnalytics()
    prices = (100.0, 200.0, 300.0)

    # First call - cache miss
    res1 = analytics.get_summary(prices)
    assert res1["mean"] == 200.0

    # Second call - cache hit
    res2 = analytics.get_summary(prices)
    assert res2 == res1

    # Invalidate cache
    initial_version = analytics.version
    analytics.invalidate()
    assert analytics.version == initial_version + 1

    # Call after invalidation
    res3 = analytics.get_summary(prices)
    assert res3 == res1
