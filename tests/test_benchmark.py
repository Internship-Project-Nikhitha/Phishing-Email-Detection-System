"""Tests for src/benchmark.py."""

import pytest

from src import benchmark as bm


def test_time_calls_calls_the_function_for_every_item_and_repeat():
    seen = []

    result = bm.time_calls(seen.append, [1, 2, 3], repeat=2)

    assert seen == [1, 2, 3, 1, 2, 3]
    assert result["messages"] == 6
    assert result["total_seconds"] > 0
    assert result["messages_per_second"] == pytest.approx(6 / result["total_seconds"])
    assert result["per_message_ms"] == pytest.approx(1000 * result["total_seconds"] / 6)


def test_time_calls_validates_input():
    with pytest.raises(ValueError, match="empty"):
        bm.time_calls(print, [])
    with pytest.raises(ValueError, match="repeat"):
        bm.time_calls(print, [1], repeat=0)


def test_measure_latency_runs_warmup_plus_timed_calls():
    calls = []

    result = bm.measure_latency(calls.append, "x", runs=10, warmup=3)

    assert len(calls) == 13
    assert result["runs"] == 10.0
    assert 0 <= result["median_ms"] <= result["p95_ms"]
    assert result["mean_ms"] >= 0


def test_measure_latency_single_run_and_validation():
    assert bm.measure_latency(lambda item: None, 1, runs=1, warmup=0)["runs"] == 1.0
    with pytest.raises(ValueError, match="runs"):
        bm.measure_latency(lambda item: None, 1, runs=0)
