"""CSV codec. Takes a binary or text handle the caller opens and closes.
Values are plain strings; typing them is the caller's job.

``import csv`` below is the standard library, not this module.
"""

import csv
import io


def read_rows(handle, *, encoding="utf-8-sig", **fmt):
    """Rows as dicts keyed by the header. The default ``utf-8-sig`` strips
    Excel's byte-order mark; pass e.g. ``"latin-1"`` for older feeds. ``fmt``
    goes to ``csv.DictReader`` (``delimiter``, ...)."""
    raw = handle.read()
    text = raw.decode(encoding) if isinstance(raw, bytes) else raw
    return list(csv.DictReader(io.StringIO(text), **fmt))


def write_rows(handle, rows, *, fieldnames=None, encoding="utf-8", **fmt):
    """Write ``rows`` with a header. ``fieldnames`` defaults to the first
    row's keys; pass it to fix the columns, or to write a header for no rows.
    Keys outside it are dropped. ``fmt`` goes to ``csv.DictWriter``."""
    rows = list(rows)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    fmt.setdefault("extrasaction", "ignore")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, **fmt)
    writer.writeheader()
    writer.writerows(rows)
    payload = buffer.getvalue()
    try:
        handle.write(payload.encode(encoding))
    except TypeError:
        handle.write(payload)
