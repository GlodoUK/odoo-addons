from odoo.tests.common import TransactionCase

from odoo.addons.pipeline import tools


class TestCodecFor(TransactionCase):
    def test_returns_codec_by_extension(self):
        self.assertIs(tools.codec_for("orders.csv"), tools.csv)
        self.assertIs(tools.codec_for("orders.xls"), tools.xls)
        self.assertIs(tools.codec_for("orders.xlsx"), tools.xlsx)

    def test_is_case_insensitive(self):
        self.assertIs(tools.codec_for("ORDERS.CSV"), tools.csv)

    def test_accepts_a_full_path(self):
        self.assertIs(tools.codec_for("/in/2026/data.xlsx"), tools.xlsx)

    def test_accepts_a_bare_extension(self):
        self.assertIs(tools.codec_for(".xls"), tools.xls)

    def test_unknown_extension_raises_valueerror(self):
        with self.assertRaises(ValueError):
            tools.codec_for("notes.txt")

    def test_codecs_share_the_row_interface(self):
        for codec in tools.CODECS.values():
            self.assertTrue(hasattr(codec, "read_rows"))
            self.assertTrue(hasattr(codec, "write_rows"))
