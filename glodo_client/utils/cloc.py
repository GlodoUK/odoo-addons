import ast
import os
import pathlib

from manifestoo_core.core_addons import is_core_addon
from manifestoo_core.odoo_series import OdooSeries, UnsupportedOdooSeries

from odoo import release
from odoo.modules import Manifest
from odoo.modules.module import MANIFEST_NAMES
from odoo.tools.cloc import DEFAULT_EXCLUDE, MAX_FILE_SIZE, VALID_EXTENSION, Cloc

DEFAULT_EXCLUDE_INCLUDE_TESTS = [
    p for p in DEFAULT_EXCLUDE if not p.startswith(("tests/", "static/tests/"))
]


class CustomCloc(Cloc):
    def summary(self):
        return {
            "code": dict(self.code),
            "errors": {m: dict(files) for m, files in self.errors.items()},
        }

    def count_modules(self, env):
        try:
            major, minor = release.version_info[:2]
            series = OdooSeries(f"{major}.{minor}")
        except (ValueError, UnsupportedOdooSeries):
            series = None

        domain = [("state", "=", "installed")]
        if env["ir.module.module"]._fields.get("imported"):
            domain.append(("imported", "=", False))
        module_list = env["ir.module.module"].search(domain).mapped("name")

        for module_name in module_list:
            if series and is_core_addon(module_name, series):
                continue
            manifest = Manifest.for_addon(module_name)
            if not manifest:
                continue
            self.count_path(manifest.path)

    # Exact copy of odoo.tools.cloc.Cloc.count_path with DEFAULT_EXCLUDE → DEFAULT_EXCLUDE_INCLUDE_TESTS

    # fmt: off
    # pylint: disable=broad-except,except-pass
    # ruff: noqa: E501
    def count_path(self, path, exclude=None):
        path = path.rstrip('/')
        exclude_list = []
        for i in MANIFEST_NAMES:
            manifest_path = os.path.join(path, i)
            try:
                with open(manifest_path, 'rb') as manifest:
                    exclude_list.extend(DEFAULT_EXCLUDE_INCLUDE_TESTS)
                    d = ast.literal_eval(manifest.read().decode('latin1'))
                    for j in ['cloc_exclude', 'demo', 'demo_xml']:
                        exclude_list.extend(d.get(j, []))
                    break
            except Exception:
                pass
        if not exclude:
            exclude = set()
        for i in filter(None, exclude_list):
            assert '..' not in i, (
                f"Invalid exclusion path '{i}': '..' is not allowed. Use a normalized path."
            )
            exclude.update(str(p) for p in pathlib.Path(path).glob(i))

        module_name = os.path.basename(path)
        self.book(module_name)
        for root, _dirs, files in os.walk(path):
            for file_name in files:
                file_path = os.path.join(root, file_name)

                if file_path in exclude:
                    continue

                ext = os.path.splitext(file_path)[1].lower()
                if ext not in VALID_EXTENSION:
                    continue

                if os.path.getsize(file_path) > MAX_FILE_SIZE:
                    self.book(module_name, file_path, (-1, "Max file size exceeded"))
                    continue

                with open(file_path, 'rb') as f:
                    # Decode using latin1 to avoid error that may raise by decoding with utf8
                    # The chars not correctly decoded in latin1 have no impact on how many lines will be counted
                    content = f.read().decode('latin1')
                self.book(module_name, file_path, self.parse(content, ext))
    # fmt: on
