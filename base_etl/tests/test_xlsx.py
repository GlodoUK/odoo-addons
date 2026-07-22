import io

from odoo.tests.common import TransactionCase

from odoo.addons.base_etl import xlsx


class TestXlsx(TransactionCase):
    def _to_bytes(self, rows, **kw):
        out = io.BytesIO()
        xlsx.write_rows(out, rows, **kw)
        return out.getvalue()

    def test_write_then_read_round_trips_and_keeps_types(self):
        rows = [{"code": "A", "qty": 1}, {"code": "B", "qty": 2}]
        # Excel carries types, so ints come back as ints (not strings).
        self.assertEqual(xlsx.read_rows(io.BytesIO(self._to_bytes(rows))), rows)

    def test_read_rows_keys_by_header(self):
        data = self._to_bytes([{"code": "A", "qty": 1}])
        self.assertEqual(xlsx.read_rows(io.BytesIO(data)), [{"code": "A", "qty": 1}])

    def test_write_rows_explicit_fieldnames_fix_order_and_subset(self):
        data = self._to_bytes(
            [{"code": "A", "qty": 1, "note": "x"}], fieldnames=["qty", "code"]
        )
        rows = xlsx.read_rows(io.BytesIO(data))
        self.assertEqual(list(rows[0].keys()), ["qty", "code"])

    def test_named_sheet_round_trips(self):
        data = self._to_bytes([{"code": "A"}], sheet="Feed")
        self.assertEqual(
            xlsx.read_rows(io.BytesIO(data), sheet="Feed"), [{"code": "A"}]
        )

    def test_empty_rows_emit_header_only(self):
        data = self._to_bytes([], fieldnames=["code", "qty"])
        self.assertEqual(xlsx.read_rows(io.BytesIO(data)), [])
