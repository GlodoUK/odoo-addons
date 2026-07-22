import io

from odoo.tests.common import TransactionCase

from odoo.addons.base_etl import csv


class TestCsv(TransactionCase):
    def test_read_rows_keys_by_header(self):
        rows = csv.read_rows(io.BytesIO(b"code,qty\nA,1\nB,2\n"))
        self.assertEqual(rows, [{"code": "A", "qty": "1"}, {"code": "B", "qty": "2"}])

    def test_read_rows_strips_bom(self):
        handle = io.BytesIO("﻿code,qty\nA,1\n".encode())
        # Without utf-8-sig the first header would be '﻿code'.
        self.assertEqual(csv.read_rows(handle), [{"code": "A", "qty": "1"}])

    def test_read_rows_accepts_a_text_handle(self):
        rows = csv.read_rows(io.StringIO("code,qty\nA,1\n"))
        self.assertEqual(rows, [{"code": "A", "qty": "1"}])

    def test_read_rows_honours_delimiter(self):
        rows = csv.read_rows(io.BytesIO(b"code;qty\nA;1\n"), delimiter=";")
        self.assertEqual(rows, [{"code": "A", "qty": "1"}])

    def test_read_rows_empty_data_is_empty(self):
        self.assertEqual(csv.read_rows(io.BytesIO(b"")), [])

    def test_write_rows_round_trips_binary_handle(self):
        rows = [{"code": "A", "qty": "1"}, {"code": "B", "qty": "2"}]
        out = io.BytesIO()
        csv.write_rows(out, rows)
        self.assertEqual(csv.read_rows(io.BytesIO(out.getvalue())), rows)

    def test_write_rows_accepts_a_text_handle(self):
        out = io.StringIO()
        csv.write_rows(out, [{"code": "A", "qty": "1"}])
        self.assertEqual(
            csv.read_rows(io.StringIO(out.getvalue())), [{"code": "A", "qty": "1"}]
        )

    def test_write_rows_infers_fieldnames_from_first_row(self):
        out = io.BytesIO()
        csv.write_rows(out, [{"code": "A", "qty": "1"}])
        self.assertTrue(out.getvalue().startswith(b"code,qty"))

    def test_write_rows_explicit_fieldnames_fix_order_and_subset(self):
        out = io.BytesIO()
        csv.write_rows(
            out, [{"code": "A", "qty": "1", "note": "x"}], fieldnames=["qty", "code"]
        )
        rows = csv.read_rows(io.BytesIO(out.getvalue()))
        self.assertEqual(list(rows[0].keys()), ["qty", "code"])

    def test_write_rows_empty_with_fieldnames_emits_header_only(self):
        out = io.BytesIO()
        csv.write_rows(out, [], fieldnames=["code", "qty"])
        self.assertEqual(out.getvalue().decode().splitlines(), ["code,qty"])
