"""Filesystem building blocks for ETL steps.

Thin helpers over an fsspec filesystem for the two file operations ETL jobs
do again and again and that take *more than one* fsspec call to get right:
list a set of files, and archive one aside. Single-call operations
(``fs.cat_file``, ``fs.pipe_file``, ``fs.mv``, ``fs.rm``, ``fs.open``) are not
wrapped -- the caller already holds ``fs`` and should just call them.

The file-driving helpers (``glob``, ``archive``, ``sweep``, ``opened``) each take
the filesystem as their first argument (``fs``). The caller owns constructing and
configuring it -- local, SFTP, S3, whatever fsspec exposes -- and these just
drive it: they import neither fsspec nor Odoo, only calling the standard fsspec
filesystem methods, so they are duck-typed over the protocol and unit-testable
against any filesystem (a ``LocalFileSystem`` on a tmp dir, an in-memory one)
with no Odoo env. ``filesystem`` is the exception -- it builds one, importing
fsspec lazily.

Paths are POSIX-style with ``/`` separators, as fsspec normalises them -- so
``posixpath`` (not ``os.path``, which follows the platform separator) is the
right tool when a caller needs the file name of a path.
"""

import datetime
import json
import posixpath
from contextlib import contextmanager


def glob(fs, pattern, *, files_only=True):
    """Full paths matching a glob ``pattern`` (fsspec syntax), sorted.

    ``pattern`` is a full path glob: ``"/in/*.csv"`` for a drop folder,
    ``"/in/**/*.csv"`` to recurse. A pattern that matches nothing (including
    an absent directory) yields ``[]`` rather than raising, so a first poll
    against an empty source is a no-op. Directories are dropped unless
    ``files_only`` is False, so the result is safe to hand straight to
    :func:`archive` (or the caller's own ``fs.open``/``fs.cat_file``). Pairs
    with :func:`archive` for the common "match the files I want and sweep each
    aside" pattern.
    """
    matches = fs.glob(pattern)
    if files_only:
        matches = (match for match in matches if fs.isfile(match))
    return sorted(matches)


def archive(fs, src, directory):
    """Move ``src`` into ``directory`` under its own name and return the new
    path, creating ``directory`` first.

    This is how a poller claims a file once handled: the move takes it out of
    the scanned folder in one step, so a slow or failing step can never leave
    it to be picked up twice. ``directory`` is used as given -- format any
    date-stamped destination (``.../2026/07/22``) before calling, keeping this
    helper clock-free and therefore deterministic to test.
    """
    if not directory:
        raise ValueError(f"archive() needs a destination directory, got {directory}")
    directory = directory.rstrip("/")
    fs.makedirs(directory, exist_ok=True)
    dst = f"{directory}/{posixpath.basename(src)}"
    fs.mv(src, dst)
    return dst


def sweep(fs, pattern, directory):
    """Archive every file matching ``pattern`` into ``directory`` in one shot,
    returning the new (archived) paths in sorted order.

    The one-shot claim, and the usual way to start a poll: it takes the whole
    matching batch out of the scanned folder *before* anything downstream runs,
    so a file is never left to be picked up by an overlapping poll, and the
    returned paths are where each file now lives -- ready to read. Equivalent
    to :func:`archive`-ing each :func:`glob` match, so a match colliding on
    name in ``directory`` is overwritten just as :func:`archive` would; keep
    ``pattern`` to a single folder (``"/in/*.csv"``) unless names are unique.
    """
    return [archive(fs, path, directory) for path in glob(fs, pattern)]


@contextmanager
def opened(fs, path, mode="wb", auto_mkdir=True, **kwargs):
    """Open ``path`` on ``fs`` in ``mode`` (default ``wb``) and yield the handle
    (closed on exit).

    ``fs.open`` alone is a single call the caller could make, but for a write
    mode ensuring the parent directory exists first (as :func:`archive` does for
    a move) is the extra step worth wrapping - so this is the write counterpart
    to :func:`sweep` on the read side. It matters because most real transports
    do *not* create it: fsspec's own ``auto_mkdir`` defaults to False on the
    local filesystem and is absent entirely on SFTP, so a write into a new
    (e.g. date-partitioned) folder would otherwise fail.

    ``auto_mkdir`` (default True) creates the parent directory for a creating
    mode (``w``/``a``/``x``); pass False to skip it when the directory is known
    to exist (e.g. to avoid the extra round-trip on SFTP). Reads never create
    anything. Any extra keyword arguments are forwarded to ``fs.open`` (e.g.
    ``block_size``, or ``autocommit=False`` for SFTP's write-to-temp-then-commit
    atomic delivery). The caller writes/reads through the yielded handle, so a
    codec can stream straight to it::

        with open(fs, "/out/2026/01/order-5.csv") as handle:
            csv.write_rows(handle, rows)
    """
    if auto_mkdir and any(flag in mode for flag in ("w", "a", "x")):
        directory = posixpath.dirname(path)
        if directory:
            fs.makedirs(directory, exist_ok=True)
    with fs.open(path, mode, **kwargs) as handle:
        yield handle


def parse_options(options):
    """``options`` (a JSON object as text, a dict, or empty) as a dict of
    fsspec keyword arguments. Raises ``ValueError`` for anything else, so a
    caller can report a bad value where it was entered."""
    if not options:
        return {}
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except ValueError as exc:
            raise ValueError(f"Storage options are not valid JSON: {exc}") from exc
    if not isinstance(options, dict):
        raise ValueError("Storage options must be a JSON object.")
    return options


def filesystem(protocol, options=None, **extra):
    """The fsspec filesystem for ``protocol``, built from ``options`` (see
    :func:`parse_options`) plus ``extra`` keyword arguments, which win - for
    values that cannot travel as JSON, like an SFTP ``pkey`` or
    ``host_key_policy`` (see :mod:`autopilot.tools.ssh`)."""
    import fsspec

    return fsspec.filesystem(protocol, **dict(parse_options(options), **extra))


def render_path(template, record=None, now=None):
    """A configured path ``template`` with its ``str.format`` tokens resolved:
    ``{datetime:...}`` against ``now`` (default: the current time) and
    ``{record.*}`` against ``record``, so any path can be date-partitioned or
    record-scoped - ``/in/processed/{datetime:%Y}/{datetime:%m}`` or
    ``/out/{record.name}-{datetime:%Y%m%dT%H%M%S}.csv``. Empty for no
    template."""
    if now is None:
        now = datetime.datetime.now().replace(microsecond=0)
    return (template or "").format(datetime=now, record=record)
