"""Reusable, Odoo-free building blocks that pipeline stages compose.

Each module is small, format/protocol-agnostic and unit-testable without an
Odoo env:

* :mod:`files` - drive an fsspec filesystem: ``glob``, ``archive``, and
  ``sweep`` (glob + archive, the one-shot "claim the batch" primitive).
* :mod:`csv`, :mod:`xls`, :mod:`xlsx` - row codecs (see below).
* :mod:`batch` - ``batched``, splitting rows into chunks for ``expand()``.

Codec pattern
-------------
``csv``, ``xls`` and ``xlsx`` are *codecs*: each exposes the same handle-based
interface - ``read_rows(handle) -> list[dict]`` and
``write_rows(handle, rows)`` - keyed on the first row as a header, and
differing only in format-specific keyword options (``csv``:
``encoding``/dialect; ``xls``/``xlsx``: ``sheet``). Because the interface is
identical, a stage can pick the codec by file extension and drive any format
through one call site; :func:`codec_for` does that lookup::

    codec = codec_for(path)                 # -> the csv / xls / xlsx module
    with fs.open(path, "rb") as handle:
        rows = codec.read_rows(handle)

Adding a format is just a new module exposing ``read_rows``/``write_rows`` and
an entry in :data:`CODECS`.
"""

import posixpath

from . import batch
from . import csv
from . import files
from . import xls
from . import xlsx

#: Row codecs keyed by lower-case file extension. Every value is a module
#: exposing the shared ``read_rows(handle)`` / ``write_rows(handle, rows)``
#: interface, so they are interchangeable at a call site.
CODECS = {
    ".csv": csv,
    ".xls": xls,
    ".xlsx": xlsx,
}


def codec_for(name):
    """Return the row codec module (:mod:`csv`, :mod:`xls` or :mod:`xlsx`) for
    ``name``, matched on its file extension, case-insensitively.

    ``name`` may be a filename, a full path, or a bare extension::

        codec_for("orders.CSV")     # -> csv
        codec_for("/in/data.xlsx")  # -> xlsx
        codec_for(".xls")           # -> xls

    Raises ``ValueError`` for an unsupported extension, naming the ones that
    are supported.
    """
    key = name.lower()
    extension = posixpath.splitext(key)[1] or key
    codec = CODECS.get(extension)
    if codec is None:
        supported = ", ".join(sorted(CODECS))
        raise ValueError(
            f"No pipeline row codec for {name!r}; supported extensions: {supported}."
        )
    return codec
