"""Filesystem building blocks for ETL steps.

Thin helpers over an fsspec filesystem for the two file operations ETL jobs
do again and again and that take *more than one* fsspec call to get right:
list a set of files, and archive one aside. Single-call operations
(``fs.cat_file``, ``fs.pipe_file``, ``fs.mv``, ``fs.rm``, ``fs.open``) are not
wrapped -- the caller already holds ``fs`` and should just call them.

The file-driving helpers (``glob``, ``archive``, ``sweep``) each take the
filesystem as their first argument (``fs``). The caller owns constructing and
configuring it -- local, SFTP, S3, whatever fsspec exposes -- and these just
drive it: they import neither fsspec nor Odoo, only calling the standard fsspec
filesystem methods, so they are duck-typed over the protocol and unit-testable
against any filesystem (a ``LocalFileSystem`` on a tmp dir, an in-memory one)
with no Odoo env. ``fsspec_providers`` is the one exception -- it reads fsspec's
registry to enumerate transports, importing fsspec lazily.

Paths are POSIX-style with ``/`` separators, as fsspec normalises them -- so
``posixpath`` (not ``os.path``, which follows the platform separator) is the
right tool when a caller needs the file name of a path.
"""

import posixpath


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
    directory = directory.rstrip("/")
    fs.makedirs(directory, exist_ok=True)
    dst = f"{directory}/{posixpath.basename(src)}"
    fs.mv(src, dst)
    return dst


# fsspec protocols that are not sensible file transports: in-memory/test,
# cache & wrapper layers, archives/read-only, and VCS/notebook/tracking
# integrations. A denylist rather than an allowlist, so a newly installed
# transport (webdav, oci, ...) shows up in fsspec_providers() with no code
# change here.
_NON_TRANSPORT_PROTOCOLS = frozenset(
    {
        "abstract",
        "asynclocal",
        "memory",
        "data",
        "cached",
        "blockcache",
        "filecache",
        "simplecache",
        "dir",
        "generic",
        "reference",
        "root",
        "tar",
        "zip",
        "libarchive",
        "git",
        "github",
        "dask",
        "jupyter",
        "jlab",
        "hf",
        "wandb",
        "dvc",
        "http",
        "https",
        "arrow_hdfs",
    }
)


def fsspec_providers():
    """Return the installed fsspec protocols that are plausible file
    transports, as sorted ``(value, label)`` pairs ready for a ``Selection``.

    fsspec's registry is filtered against a denylist of protocols that are not
    real transports -- in-memory and test filesystems, cache/wrapper layers,
    archives, and VCS/notebook integrations -- so only the likes of ``file``,
    ``sftp`` and ``s3`` are offered. It is a denylist, not an allowlist, so a
    newly installed backend appears on its own. Returns ``[]`` if fsspec is
    unavailable.

    This lists what fsspec *knows*; whether the chosen backend's package is
    installed is a separate check the consumer makes (e.g. via
    ``fsspec.get_filesystem_class``) when a protocol is actually used. A model
    typically prepends its own sentinel::

        protocol = fields.Selection(
            selection=lambda self: [("disabled", "Disabled")]
            + autopilot.tools.files.fsspec_providers(),
        )
    """
    try:
        import fsspec

        available = fsspec.available_protocols()
    except (ImportError, AttributeError):
        return []
    return [
        (protocol, protocol)
        for protocol in sorted(available)
        if protocol not in _NON_TRANSPORT_PROTOCOLS
    ]


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
