"""Helpers for the file steps that take more than one fsspec call to get
right. For single calls (``fs.mv``, ``fs.cat_file``, ...) use ``fs`` directly.

Each takes the filesystem first; the caller builds it. Paths use ``/``, so
reach for ``posixpath``, not ``os.path``.
"""

import datetime
import json
import posixpath
from contextlib import contextmanager


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


@contextmanager
def opened(fs, path, mode="wb", auto_mkdir=True, **kwargs):
    """``fs.open``, creating the parent folder first when writing. Most
    transports don't: fsspec's local filesystem won't by default and SFTP
    can't, so a write into a new dated folder would fail. ``kwargs`` go to
    ``fs.open``."""
    if auto_mkdir and any(flag in mode for flag in ("w", "a", "x")):
        directory = posixpath.dirname(path)
        if directory:
            fs.makedirs(directory, exist_ok=True)
    with fs.open(path, mode, **kwargs) as handle:
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
