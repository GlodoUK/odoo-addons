"""Split an iterable into fixed-size chunks.

The input side of a pipeline's ``expand()`` fan-out: chunk a large parsed set
(CSV/XLSX rows) so each chunk becomes its own downstream job with a bounded,
serialisable payload, rather than one job carrying everything. "Split a CSV"
is then ``batched(csv.read_rows(data), 500)``.
"""

from itertools import islice


def batched(iterable, size):
    """Yield lists of up to ``size`` consecutive items from ``iterable`` until
    it is exhausted (the last chunk may be shorter).

    Like ``itertools.batched`` on 3.12+, but yields mutable lists (friendlier
    as queue_job payloads) and works on older Pythons. ``size`` must be >= 1.
    """
    if size < 1:
        raise ValueError("size must be at least 1")
    iterator = iter(iterable)
    while chunk := list(islice(iterator, size)):
        yield chunk
