"""XLS codec for pipeline stages: a file handle <-> a list of row dicts.

The legacy-Excel (BIFF ``.xls``) sibling of :mod:`.xlsx`, with the same
handle-based, first-row-is-header contract. Reading uses ``xlrd`` and writing
uses ``xlwt`` (xlrd cannot write) -- both ship with Odoo. Both functions take
an open **binary** file handle; ``open(..., "rb"/"wb")``,
``fsspec.open(..., "rb"/"wb")`` and ``io.BytesIO()`` all work, and the caller
owns opening/closing. Nothing here imports Odoo, so it is unit-testable on an
in-memory handle.

Legacy ``.xls`` is less typed than ``.xlsx``: xlrd returns every number as a
``float`` (so ``1`` round-trips as ``1.0``), and the format has no typed null,
so a ``None`` or missing value is written as a blank cell that reads back as
``""``. Emit ``.xlsx`` (or ``.csv``) for new files; ``.xls`` is really a
receive-side format for old systems.
"""

import xlrd
import xlwt


def read_rows(handle, *, sheet=None):
    """Parse the workbook in ``handle`` into a list of dicts keyed by the
    header row of ``sheet`` (its name; the first sheet when omitted).

    ``handle`` is a readable binary file object (its bytes are read in full and
    handed to xlrd, which has no streaming mode). An empty sheet (no header
    row) yields ``[]``. Numbers come back as ``float`` -- see the module note.
    The rows are materialised before returning, so the caller's handle can
    close straight after::

        with fs.open(path, "rb") as handle:
            rows = read_rows(handle)
    """
    workbook = xlrd.open_workbook(file_contents=handle.read())
    try:
        worksheet = (
            workbook.sheet_by_name(sheet) if sheet else workbook.sheet_by_index(0)
        )
        if worksheet.nrows == 0:
            return []
        header = worksheet.row_values(0)
        return [
            dict(zip(header, worksheet.row_values(index), strict=False))
            for index in range(1, worksheet.nrows)
        ]
    finally:
        # Frees xlrd's buffers, not the caller's handle.
        workbook.release_resources()


def write_rows(handle, rows, *, fieldnames=None, sheet=None):
    """Write ``rows`` (an iterable of dicts) to ``handle`` as an ``.xls``
    workbook with a header row.

    ``handle`` is a writable binary file object. ``fieldnames`` defaults to the
    keys of the first row, in order; pass it explicitly to fix the column
    order/subset, or to emit just a header when ``rows`` is empty. ``sheet``
    names the worksheet (``"Sheet1"`` when omitted). A ``None`` or missing
    value is written as a blank cell -- see the module note::

        with fs.open(path, "wb") as handle:
            write_rows(handle, rows)
    """
    rows = list(rows)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet(sheet or "Sheet1")
    for column, name in enumerate(fieldnames):
        worksheet.write(0, column, name)
    for index, row in enumerate(rows, start=1):
        for column, name in enumerate(fieldnames):
            value = row.get(name)
            worksheet.write(index, column, "" if value is None else value)
    workbook.save(handle)
