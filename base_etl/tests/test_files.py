import logging
import posixpath
import shutil
import tempfile
import unittest

from odoo.tests.common import TransactionCase

from odoo.addons.base_etl import files

_logger = logging.getLogger(__name__)

try:
    from fsspec.implementations.local import LocalFileSystem
except ImportError:
    LocalFileSystem = None
    _logger.info("fsspec not installed; skipping %s", __name__)


@unittest.skipUnless(LocalFileSystem is not None, "fsspec is not installed")
class TestFiles(TransactionCase):
    """The fs helpers are pure fsspec drivers, so they run against a real
    LocalFileSystem on a throwaway directory -- no Odoo env involved."""

    def setUp(self):
        super().setUp()
        self.fs = LocalFileSystem(auto_mkdir=True)
        self.root = tempfile.mkdtemp(prefix="base_etl-files-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def _write(self, relpath, data=b"x"):
        path = f"{self.root}/{relpath}"
        with self.fs.open(path, "wb") as handle:
            handle.write(data)
        return path

    def test_glob_absent_directory_is_empty(self):
        self.assertEqual(files.glob(self.fs, f"{self.root}/nope/*.csv"), [])

    def test_glob_filters_by_pattern_and_skips_dirs(self):
        self._write("in/a.csv")
        self._write("in/b.csv")
        self._write("in/note.txt")
        self.fs.makedirs(f"{self.root}/in/sub", exist_ok=True)
        found = files.glob(self.fs, f"{self.root}/in/*.csv")
        self.assertEqual([posixpath.basename(p) for p in found], ["a.csv", "b.csv"])

    def test_glob_single_star_is_not_recursive(self):
        self._write("in/top.csv")
        self._write("in/sub/deep.csv")
        found = files.glob(self.fs, f"{self.root}/in/*.csv")
        self.assertEqual([posixpath.basename(p) for p in found], ["top.csv"])

    def test_glob_recurses_with_double_star(self):
        self._write("in/top.csv")
        self._write("in/sub/deep.csv")
        found = files.glob(self.fs, f"{self.root}/in/**/*.csv")
        self.assertEqual(
            [posixpath.basename(p) for p in found], ["deep.csv", "top.csv"]
        )

    def test_glob_can_include_directories(self):
        self._write("in/a.csv")
        self.fs.makedirs(f"{self.root}/in/sub", exist_ok=True)
        found = files.glob(self.fs, f"{self.root}/in/*", files_only=False)
        self.assertIn("sub", [posixpath.basename(p) for p in found])

    def test_providers_lists_transports_and_drops_non_transports(self):
        providers = files.fsspec_providers()
        # Sorted (value, label) pairs, value == label.
        self.assertTrue(all(isinstance(p, tuple) and p[0] == p[1] for p in providers))
        values = [value for value, _label in providers]
        self.assertEqual(values, sorted(values))
        # "file" is a real transport; "memory" is denylisted.
        self.assertIn("file", values)
        self.assertNotIn("memory", values)

    def test_archive_moves_into_directory_under_same_name(self):
        src = self._write("in/a.csv", b"payload")
        dst = files.archive(self.fs, src, f"{self.root}/archive/2026/07")
        self.assertEqual(dst, f"{self.root}/archive/2026/07/a.csv")
        self.assertFalse(self.fs.exists(src))
        with self.fs.open(dst, "rb") as handle:
            self.assertEqual(handle.read(), b"payload")

    def test_sweep_claims_matches_into_directory(self):
        self._write("in/a.csv", b"A")
        self._write("in/b.csv", b"B")
        self._write("in/skip.txt", b"T")
        processed = f"{self.root}/processed"

        claimed = files.sweep(self.fs, f"{self.root}/in/*.csv", processed)

        # Both CSVs were moved out of the drop folder, in sorted order, and the
        # unmatched .txt was left untouched.
        self.assertEqual(claimed, [f"{processed}/a.csv", f"{processed}/b.csv"])
        self.assertEqual(files.glob(self.fs, f"{self.root}/in/*.csv"), [])
        self.assertTrue(self.fs.exists(f"{self.root}/in/skip.txt"))
        with self.fs.open(claimed[0], "rb") as handle:
            self.assertEqual(handle.read(), b"A")

    def test_sweep_no_matches_is_noop(self):
        self.assertEqual(
            files.sweep(self.fs, f"{self.root}/in/*.csv", f"{self.root}/processed"),
            [],
        )
