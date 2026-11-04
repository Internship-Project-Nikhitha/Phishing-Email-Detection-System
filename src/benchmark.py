"""Simple timing helpers for latency and throughput (Member 1).

These measure how long a function takes on a documented set of inputs. Results
depend on the computer they run on, so always report the machine and dataset.
"""

import statistics
import time
from collections.abc import Callable, Sequence
from typing import Any


def time_calls(function: Callable[[Any], Any], items: Sequence[Any], repeat: int = 1) -> dict[str, float]:
    """Time ``function`` over every item (``repeat`` times) and report throughput.

    Returns:
        ``total_seconds``, ``messages`` (number of calls), ``per_message_ms``
        and ``messages_per_second``.

    Raises:
        ValueError: If ``items`` is empty or ``repeat`` is less than 1.
    """
    if not items:
        raise ValueError("items must not be empty.")
    if repeat < 1:
        raise ValueError("repeat must be at least 1.")
    started = time.perf_counter()
    for _ in range(repeat):
        for item in items:
            function(item)
    total = max(time.perf_counter() - started, 1e-9)
    messages = len(items) * repeat
    return {
        "total_seconds": total,
        "messages": messages,
        "per_message_ms": 1000 * total / messages,
        "messages_per_second": messages / total,
    }


def measure_latency(function: Callable[[Any], Any], item: Any, runs: int = 20, warmup: int = 2) -> dict[str, float]:
    """Time single calls of ``function(item)`` and report median, mean and 95th percentile.

    Args:
        function: The function to time.
        item: The input to pass every time.
        runs: Number of timed calls (at least 1).
        warmup: Untimed calls first, to avoid counting one-off start-up work.

    Returns:
        ``median_ms``, ``mean_ms``, ``p95_ms`` and ``runs``.
    """
    if runs < 1:
        raise ValueError("runs must be at least 1.")
    for _ in range(max(warmup, 0)):
        function(item)
    durations = []
    for _ in range(runs):
        started = time.perf_counter()
        function(item)
        durations.append(1000 * (time.perf_counter() - started))
    durations.sort()
    p95_index = min(len(durations) - 1, max(0, round(0.95 * len(durations)) - 1))
    return {
        "median_ms": statistics.median(durations),
        "mean_ms": statistics.mean(durations),
        "p95_ms": durations[p95_index],
        "runs": float(runs),
    }
