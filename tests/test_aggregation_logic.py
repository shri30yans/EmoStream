"""Unit tests for the window-aggregation math (no Spark needed)."""

from streaming.aggregation import aggregate_window, downsample_count


def test_downsample_boundaries():
    assert downsample_count(0) == 0
    assert downsample_count(1) == 1
    assert downsample_count(1000) == 1
    assert downsample_count(1001) == 1
    assert downsample_count(2500) == 2
    assert downsample_count(1_000_000) == 1000


def test_custom_per_unit():
    assert downsample_count(500, per_unit=100) == 5


def test_aggregate_window_sorts_by_volume():
    payload = aggregate_window({"cheer": 50, "wow": 5000, "heart": 5})
    assert [row["reaction"] for row in payload] == ["wow", "cheer", "heart"]
    assert payload[0] == {"reaction": "wow", "count": 5, "raw_count": 5000}
