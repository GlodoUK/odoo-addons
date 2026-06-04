"""
Generating new migration files (`odoo shoehorn generate`).

The naming convention (FILENAME_RE etc.) is defined in migration.py.
"""

import datetime
import os
import re

from .migration import EXTENSIONS, FILENAME_RE, TIMESTAMP_FORMAT

TEMPLATES = {
    "py": "def up(env):\n    pass\n",
    "xml": '<?xml version="1.0" encoding="UTF-8" ?>\n<odoo>\n</odoo>\n',
    "csv": "",
    "sql": "",
}


def generate(directory, name):
    """Create a new migration file in `directory` and return its path."""
    base, ext = os.path.splitext(name)
    ext = (ext.lstrip(".") or "py").lower()
    if ext not in EXTENSIONS:
        raise ValueError(f"Migrations can't have a .{ext} extension.")
    base = re.sub(r"[\s-]+", "_", base.strip().lower())
    version = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
    filename = f"{version}_{base}.{ext}"
    if not FILENAME_RE.match(filename):
        raise ValueError(f"'{name}' does not make a valid migration name.")
    path = os.path.join(os.path.abspath(directory), filename)
    with open(path, "x") as f:
        f.write(TEMPLATES[ext])
    return path
