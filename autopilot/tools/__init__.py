"""Odoo-free ETL helpers: no model or ``odoo`` import belongs here, so they
can be tested on an in-memory handle.

``csv``, ``xls`` and ``xlsx`` are interchangeable codecs: ``read_rows`` and
``write_rows`` over a file handle, keyed on a header row. ``codec_for`` picks
one by extension. A new format is a module with those two functions, added to
``CODECS``.
"""

import posixpath

from . import batch
from . import csv
from . import files
from . import ssh
from . import xls
from . import xlsx

CODECS = {
    ".csv": csv,
    ".xls": xls,
    ".xlsx": xlsx,
}


def codec_for(name):
    """The codec for ``name``: a filename, path or bare extension, any case."""
    key = name.lower()
    extension = posixpath.splitext(key)[1] or key
    codec = CODECS.get(extension)
    if codec is None:
        supported = ", ".join(sorted(CODECS))
        raise ValueError(
            f"No autopilot.tools row codec for {name!r}; "
            f"supported extensions: {supported}."
        )
    return codec
