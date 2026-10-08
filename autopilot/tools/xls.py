"""Old Excel ``.xls`` codec, over a binary handle.

Watch out: every number reads back as a float (``1`` becomes ``1.0``), and
``None`` is written as a blank cell that reads back as ``""``. Write ``.xlsx``
or ``.csv`` for new files; ``.xls`` is for receiving from older systems.
"""

import xlrd
import xlwt


def read_rows(handle, *, sheet=None):
    """Rows of ``sheet`` (default: the first) keyed by its header row. The
    whole file is read into memory."""
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
        workbook.release_resources()


def write_rows(handle, rows, *, fieldnames=None, sheet=None):
    """Write ``rows`` with a header, as for the CSV codec."""
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
