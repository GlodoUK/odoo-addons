"""Chunks for fan-out: one job per ``batched(rows, 500)``, not one job
carrying everything."""

from itertools import islice


def batched(iterable, size):
    """``itertools.batched``, but yielding lists, which queue_job serialises."""
    if size < 1:
        raise ValueError("size must be at least 1")
    iterator = iter(iterable)
    while chunk := list(islice(iterator, size)):
        yield chunk
