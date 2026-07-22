"""CSV codec for pipeline stages: a file handle <-> a list of row dicts.

The bytes/rows boundary is the same several-step dance in every connector --
decode (stripping the Excel BOM), wrap in a text buffer, drive csv's
DictReader/DictWriter -- so it lives here once. Both functions take an open
file handle rather than bytes, so the caller owns opening/closing and the
transport: ``open(...)``, ``fsspec.open(...)`` and ``io.BytesIO()`` all work,
and either a binary (``rb``/``wb``) or text (``r``/``w``) handle is accepted.
Values are read and written as plain strings; typing and validation are the
caller's job. Nothing here imports Odoo, so it is unit-testable on an
in-memory handle.

``import csv`` below is the Python standard library (absolute imports), not
this module.
"""

import csv
import io


def read_rows(handle, *, encoding="utf-8-sig", **fmt):
    """Parse the CSV in ``handle`` into a list of dicts keyed by the header
    row.

    ``handle`` is any readable file object; bytes read from a binary handle
    are decoded with ``encoding`` (default ``utf-8-sig``, so a leading
    byte-order mark from Excel is stripped -- pass e.g. ``"latin-1"`` for
    legacy feeds), while a text handle is read as-is. ``**fmt`` is forwarded to
    ``csv.DictReader`` (``delimiter``, ``quotechar``, ...). The whole handle is
    consumed but not closed -- that stays with the caller's ``with`` block::

        with fs.open(path, "rb") as handle:
            rows = read_rows(handle)
    """
    raw = handle.read()
    text = raw.decode(encoding) if isinstance(raw, bytes) else raw
    return list(csv.DictReader(io.StringIO(text), **fmt))


def write_rows(handle, rows, *, fieldnames=None, encoding="utf-8", **fmt):
    """Write ``rows`` (an iterable of dicts) to ``handle`` as CSV with a header.

    ``handle`` is any writable file object; the payload is written as bytes to
    a binary handle (encoded with ``encoding``) or as text to a text handle.
    ``fieldnames`` defaults to the keys of the first row, in order; pass it
    explicitly to fix the column order/subset, or to emit a header row when
    ``rows`` is empty. ``**fmt`` is forwarded to ``csv.DictWriter``. The handle
    is written to but not closed::

        with fs.open(path, "wb") as handle:
            write_rows(handle, rows)
    """
    rows = list(rows)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    # Default to dropping keys outside `fieldnames` so an explicit subset
    # works; a caller can pass extrasaction="raise" to forbid extras instead.
    fmt.setdefault("extrasaction", "ignore")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, **fmt)
    writer.writeheader()
    writer.writerows(rows)
    payload = buffer.getvalue()
    try:
        handle.write(payload.encode(encoding))
    except TypeError:
        # A text-mode handle rejects bytes; write the string instead.
        handle.write(payload)
