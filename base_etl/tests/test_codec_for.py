from odoo.tests.common import TransactionCase

from odoo.addons import base_etl


class TestCodecFor(TransactionCase):
    def test_returns_codec_by_extension(self):
        self.assertIs(base_etl.codec_for("orders.csv"), base_etl.csv)
        self.assertIs(base_etl.codec_for("orders.xls"), base_etl.xls)
        self.assertIs(base_etl.codec_for("orders.xlsx"), base_etl.xlsx)

    def test_is_case_insensitive(self):
        self.assertIs(base_etl.codec_for("ORDERS.CSV"), base_etl.csv)

    def test_accepts_a_full_path(self):
        self.assertIs(base_etl.codec_for("/in/2026/data.xlsx"), base_etl.xlsx)

    def test_accepts_a_bare_extension(self):
        self.assertIs(base_etl.codec_for(".xls"), base_etl.xls)

    def test_unknown_extension_raises_valueerror(self):
        with self.assertRaises(ValueError):
            base_etl.codec_for("notes.txt")

    def test_codecs_share_the_row_interface(self):
        for codec in base_etl.CODECS.values():
            self.assertTrue(hasattr(codec, "read_rows"))
            self.assertTrue(hasattr(codec, "write_rows"))
