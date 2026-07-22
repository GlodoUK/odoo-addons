Pipeline tools
==============

``pipeline.tools`` bundles the small helpers that file-based integrations keep
re-inventing. Each takes its dependency explicitly -- an fsspec filesystem, or
an open file handle -- so it stays transport-agnostic and easy to unit-test
without an Odoo environment. Import the package and reach for what you need::

    from odoo.addons.pipeline import tools

    tools.files.sweep(fs, "/in/*.csv", "/in/processed")
    tools.codec_for(path).read_rows(handle)

Files
-----

``tools.files`` drives any fsspec filesystem -- local, SFTP, S3, whatever is
installed:

* ``glob(fs, pattern)`` -- sorted paths matching a glob (``*`` or ``**``), with
  directories dropped. An empty match returns ``[]`` rather than raising, so a
  first poll against an empty source is a no-op.
* ``archive(fs, src, directory)`` -- move a file into ``directory`` under its
  own name (creating the directory) and return the new path.
* ``sweep(fs, pattern, directory)`` -- glob and archive in one step. This is the
  "claim this batch" move a poll opens with: a file taken out of the source
  cannot be picked up twice.
* ``fsspec_providers()`` -- the installed fsspec protocols worth offering as a
  transport (``file``, ``sftp``, ``s3``, ...), as ``(value, label)`` pairs for a
  ``Selection`` field. In-memory, cache, archive and VCS protocols are filtered
  out; a model usually prepends its own sentinel::

      protocol = fields.Selection(
          selection=lambda self: [("disabled", "Disabled")]
          + tools.files.fsspec_providers(),
      )

Row codecs
----------

``tools.csv``, ``tools.xls`` and ``tools.xlsx`` are three codecs behind one
interface. Each reads and writes a list of row dicts, keyed on the first row as
a header:

* ``read_rows(handle) -> list[dict]``
* ``write_rows(handle, rows)``

They take an open file handle, so the caller owns opening, closing and the
transport. ``csv`` accepts either a text or binary handle and strips the Excel
BOM; ``xls`` (via ``xlrd``/``xlwt``) and ``xlsx`` (via ``openpyxl``) take a
binary handle. Legacy ``.xls`` is less typed than the others -- numbers come
back as floats -- so prefer ``.xlsx`` or ``.csv`` for files you create.

Because the interface is identical, ``tools.codec_for(path)`` picks the right
codec by file extension and a stage stays format-agnostic::

    codec = tools.codec_for(path)          # -> the csv / xls / xlsx module
    with fs.open(path, "rb") as handle:
        rows = codec.read_rows(handle)

Adding a format is a new module exposing ``read_rows``/``write_rows`` plus an
entry in ``tools.CODECS``.

Batching
--------

``tools.batch.batched(iterable, size)`` splits an iterable into fixed-size
lists. This is the input side of ``expand()``: chunk rows so each downstream job
carries a bounded, serialisable payload.
