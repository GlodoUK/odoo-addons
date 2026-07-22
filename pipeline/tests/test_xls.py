import io

from odoo.tests.common import TransactionCase

from odoo.addons.pipeline.tools import xls


class TestXlsTools(TransactionCase):
    def _to_bytes(self, rows, **kw):
        out = io.BytesIO()
        xls.write_rows(out, rows, **kw)
        return out.getvalue()

    def test_write_then_read_round_trips_strings(self):
        rows = [{"code": "A", "note": "x"}, {"code": "B", "note": "y"}]
        self.assertEqual(xls.read_rows(io.BytesIO(self._to_bytes(rows))), rows)

    def test_numbers_come_back_as_float(self):
        # Legacy .xls has one numeric type, so xlrd yields float (see module).
        data = self._to_bytes([{"qty": 1}])
        self.assertEqual(xls.read_rows(io.BytesIO(data)), [{"qty": 1.0}])

    def test_write_rows_explicit_fieldnames_fix_order_and_subset(self):
        data = self._to_bytes(
            [{"code": "A", "qty": "1", "note": "x"}], fieldnames=["qty", "code"]
        )
        rows = xls.read_rows(io.BytesIO(data))
        self.assertEqual(list(rows[0].keys()), ["qty", "code"])

    def test_named_sheet_round_trips(self):
        data = self._to_bytes([{"code": "A"}], sheet="Feed")
        self.assertEqual(xls.read_rows(io.BytesIO(data), sheet="Feed"), [{"code": "A"}])

    def test_empty_rows_emit_header_only(self):
        data = self._to_bytes([], fieldnames=["code", "qty"])
        self.assertEqual(xls.read_rows(io.BytesIO(data)), [])
