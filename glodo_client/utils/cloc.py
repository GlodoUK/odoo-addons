import os

from manifestoo_core.core_addons import is_core_addon
from manifestoo_core.odoo_series import OdooSeries, UnsupportedOdooSeries

import odoo
from odoo.modules import Manifest
from odoo.tools.cloc import VALID_EXTENSION, Cloc


def _odoo_series():
    """Return the running Odoo series, or ``None`` if manifestoo_core
    has no data for it (e.g. running master before a release)."""
    major, minor = odoo.release.version_info[:2]
    try:
        return OdooSeries(f"{major}.{minor}")
    except (ValueError, UnsupportedOdooSeries):
        return None


def _is_custom_module(module_name, series):
    """Custom = not a known CE/EE addon for this Odoo series.

    Assumes custom modules never reuse a core/enterprise addon name.
    If ``series`` is ``None`` (unknown to manifestoo_core), nothing is
    treated as core — the caller will count every installed module.
    """
    if series is None:
        return True
    return not is_core_addon(module_name, series)


def _iter_custom_module_paths(env):
    """Yield ``(module_name, path)`` for each installed custom module."""
    series = _odoo_series()
    domain = [("state", "=", "installed")]
    if env["ir.module.module"]._fields.get("imported"):
        domain.append(("imported", "=", False))
    module_names = env["ir.module.module"].search(domain).mapped("name")

    for module_name in module_names:
        if not _is_custom_module(module_name, series):
            continue
        manifest = Manifest.for_addon(module_name)
        if not manifest:
            continue
        yield module_name, manifest.path


class CustomCloc(Cloc):
    """
    Two deviations from core odoo.tools.cloc.Cloc:

    1. ``count_modules`` keeps only modules whose names are *not* known
       CE/EE addons for the running Odoo series (per ``manifestoo_core``).
       This avoids relying on ``os.path.realpath`` and the doodba-style
       ``addons/`` vs ``enterprise/`` directory heuristic.
    2. ``count_tests`` walks the ``tests/`` and ``static/tests/`` trees that
       core ``DEFAULT_EXCLUDE`` skips, and records the result in
       ``self.tests_code`` — kept separate from ``self.code`` so the non-test
       numbers still match ``odoo-bin cloc`` exactly.
    """

    def __init__(self):
        super().__init__()
        self.tests_code = {}

    def count_modules(self, module_paths):
        for _module_name, path in module_paths:
            self.count_path(path)

    def count_tests(self, module_paths):
        """Record test-tree LOC per module in ``self.tests_code``.

        Walks ``tests/`` and ``static/tests/`` under each custom module,
        counting files with extensions core ``Cloc`` would otherwise count.
        """
        for module_name, path in module_paths:
            total = 0
            for sub in ("tests", "static/tests"):
                sub_path = os.path.join(path, sub)
                if not os.path.isdir(sub_path):
                    continue
                for root, _dirs, files in os.walk(sub_path):
                    for fname in files:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in VALID_EXTENSION:
                            continue
                        file_path = os.path.join(root, fname)
                        try:
                            with open(file_path, "rb") as f:
                                content = f.read().decode("latin1")
                        except OSError:
                            continue
                        parsed = self.parse(content, ext)
                        if not parsed:
                            continue
                        loc, _file_total = parsed
                        if isinstance(loc, int) and loc > 0:
                            total += loc
            if total:
                self.tests_code[module_name] = total


def count(env) -> dict:
    """Return a structured CLOC payload for the given environment.

    Shape::

        {
            "modules":       {module_name: loc, ...},  # source-tree + tests
            "customization": {module_name: loc, ...},  # studio / manual / imported
            "errors":        {module_name: {file: error_msg, ...}, ...},
        }

    ``modules`` includes test-tree LOC (``tests/`` and ``static/tests/``) folded
    into each module's count. ``customization`` values are the delta added by
    ``count_customization`` on top of ``count_modules`` per module. Totals are
    intentionally not computed here — the server tallies them so it can apply
    per-instance module exclusions.
    """
    module_paths = list(_iter_custom_module_paths(env))
    cl = CustomCloc()
    cl.count_modules(module_paths)
    cl.count_tests(module_paths)
    for module_name, test_loc in cl.tests_code.items():
        cl.code[module_name] = cl.code.get(module_name, 0) + test_loc

    modules_snapshot = dict(cl.code)
    cl.count_customization(env)

    customization = {}
    for module_name, total_loc in cl.code.items():
        delta = total_loc - modules_snapshot.get(module_name, 0)
        if delta:
            customization[module_name] = delta

    errors = {m: dict(files) for m, files in cl.errors.items()}

    return {
        "modules": modules_snapshot,
        "customization": customization,
        "errors": errors,
    }
