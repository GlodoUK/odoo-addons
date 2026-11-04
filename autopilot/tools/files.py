"""Helpers for the file steps that take more than one fsspec call to get
right. For single calls (``fs.mv``, ``fs.cat_file``, ...) use ``fs`` directly.

Each takes the filesystem first; the caller builds it. Paths use ``/``, so
reach for ``posixpath``, not ``os.path``.
"""

import datetime
import json
import logging
import posixpath
from contextlib import contextmanager

_logger = logging.getLogger(__name__)


def glob(fs, pattern, *, files_only=True):
    """Sorted paths matching ``pattern`` (``/in/*.csv``; ``**`` recurses).
    A missing folder gives ``[]``."""
    matches = fs.glob(pattern)
    if files_only:
        matches = (match for match in matches if fs.isfile(match))
    return sorted(matches)


def archive(fs, src, directory):
    """Move ``src`` into ``directory`` (created if needed) and return its new
    path. Render any date tokens in ``directory`` first."""
    if not directory:
        raise ValueError(f"archive() needs a destination directory, got {directory}")
    directory = directory.rstrip("/")
    fs.makedirs(directory, exist_ok=True)
    dst = f"{directory}/{posixpath.basename(src)}"
    fs.mv(src, dst)
    return dst


def sweep(fs, pattern, directory):
    """Claim a poll's files: move every match into ``directory`` before
    anything reads them, so an overlapping poll can't take one twice. Returns
    the new paths.

    Watch out: a name already in ``directory`` is overwritten. Keep
    ``pattern`` to one folder unless names are unique.
    """
    return [archive(fs, path, directory) for path in glob(fs, pattern)]


def collect(fs, pattern):
    """Read a poll's files where they are, for a folder you can't move files
    out of: ``[(path, bytes)]``, sorted. Nothing claims them, so the caller
    must skip any it already has, then ``remove_collected``. A file that
    won't read is logged and left for the next poll, as is an empty one: it
    is likely still being written."""
    collected = []
    for path in glob(fs, pattern):
        try:
            data = fs.cat_file(path)
        except Exception:
            _logger.exception("Could not read %s; leaving it for the next poll.", path)
            continue
        if data:
            collected.append((path, data))
    return collected


def remove_collected(fs, collected):
    """Delete each ``(path, bytes)`` from ``collect`` whose file still holds
    those bytes. One rewritten since, as when a partner overwrites or appends
    to a fixed name, is left for the next poll. Never raises: a failure is
    logged and the file stays. Returns the paths left."""
    left = []
    for path, data in collected:
        try:
            if fs.cat_file(path) != data:
                _logger.info("%s changed since it was read; leaving it.", path)
                left.append(path)
                continue
            fs.rm_file(path)
        except Exception:
            _logger.exception("Could not delete %s.", path)
            left.append(path)
    return left


@contextmanager
def opened(fs, path, mode="wb", auto_mkdir=True, **kwargs):
    """``fs.open``, creating the parent folder when writing into one that's
    missing, such as a new dated folder: fsspec's local filesystem won't by
    default and SFTP can't. Only on a missing folder: SFTP's ``makedirs``
    walks every parent, which a server confining us to one folder may answer
    by dropping the session. ``kwargs`` go to ``fs.open``."""
    try:
        handle = fs.open(path, mode, **kwargs)
    except FileNotFoundError:
        directory = posixpath.dirname(path)
        writing = any(flag in mode for flag in ("w", "a", "x"))
        if not (auto_mkdir and writing and directory):
            raise
        fs.makedirs(directory, exist_ok=True)
        handle = fs.open(path, mode, **kwargs)
    with handle:
        yield handle


def parse_options(options):
    """fsspec options from JSON text, a dict, or nothing. ``ValueError``
    otherwise."""
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
    """The fsspec filesystem for ``protocol``. ``extra`` wins over
    ``options``; use it for values JSON can't carry, like an SFTP ``pkey``."""
    import fsspec

    return fsspec.filesystem(protocol, **dict(parse_options(options), **extra))


def render_path(template, record=None, now=None):
    """``template`` with ``{datetime:...}`` and ``{record.*}`` filled in, e.g.
    ``/out/{record.name}-{datetime:%Y%m%dT%H%M%S}.csv``."""
    if now is None:
        now = datetime.datetime.now().replace(microsecond=0)
    return (template or "").format(datetime=now, record=record)
