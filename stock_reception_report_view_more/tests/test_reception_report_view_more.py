from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestReceptionReportViewMore(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.product = cls.env["product.product"].create(
            {"name": "View More Product", "is_storable": True}
        )
        cls.partner = cls.env["res.partner"].create({"name": "View More Partner"})
        cls.report = cls.env["report.stock.report_reception"]

        cls.receipt = cls._make_picking(
            cls.warehouse.in_type_id,
            cls.env.ref("stock.stock_location_suppliers"),
            cls.warehouse.lot_stock_id,
            5,
        )
        cls.out_early = cls._make_picking(
            cls.warehouse.out_type_id,
            cls.warehouse.lot_stock_id,
            cls.env.ref("stock.stock_location_customers"),
            5,
        )
        cls.out_late = cls._make_picking(
            cls.warehouse.out_type_id,
            cls.warehouse.lot_stock_id,
            cls.env.ref("stock.stock_location_customers"),
            5,
        )

    @classmethod
    def _make_picking(cls, picking_type, src, dest, qty):
        picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": src.id,
                "location_dest_id": dest.id,
                "partner_id": cls.partner.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": qty,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": src.id,
                            "location_dest_id": dest.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        return picking

    def _move_outs(self, data):
        return self.env["stock.move"].union(
            *(
                line["move_out"]
                for lines in data["sources_to_lines"].values()
                for line in lines
            )
        )

    def test_standard_report_stops_when_receipt_is_used_up(self):
        data = self.report._get_report_values(self.receipt.ids)
        self.assertEqual(self._move_outs(data), self.out_early.move_ids)

    def test_view_more_lists_later_transfers(self):
        data = self.report.with_context(
            reception_report_view_more=True
        )._get_report_values(self.receipt.ids)
        self.assertEqual(
            self._move_outs(data), self.out_early.move_ids | self.out_late.move_ids
        )
        extra = [
            line
            for lines in data["sources_to_lines"].values()
            for line in lines
            if line.get("is_extra")
        ]
        self.assertEqual(len(extra), 1)
        self.assertEqual(extra[0]["move_out"], self.out_late.move_ids)
        self.assertEqual(extra[0]["quantity"], 5)
        self.assertEqual(extra[0]["move_ins"], self.receipt.move_ids.ids)

    def test_partial_line_reports_full_quantity(self):
        self.out_early.move_ids.product_uom_qty = 8
        data = self.report.with_context(
            reception_report_view_more=True
        )._get_report_values(self.receipt.ids)
        line = next(
            line
            for lines in data["sources_to_lines"].values()
            for line in lines
            if line["move_out"] == self.out_early.move_ids
        )
        self.assertEqual(line["quantity"], 5)
        self.assertEqual(line["full_quantity"], 8)

    def test_extra_line_reports_full_quantity(self):
        self.out_late.move_ids.product_uom_qty = 8
        data = self.report.with_context(
            reception_report_view_more=True
        )._get_report_values(self.receipt.ids)
        extra = next(
            line
            for lines in data["sources_to_lines"].values()
            for line in lines
            if line.get("is_extra")
        )
        self.assertEqual(extra["quantity"], 5)
        self.assertEqual(extra["full_quantity"], 8)

    def test_get_report_data_includes_extra_lines(self):
        data = self.report.get_report_data(self.receipt.ids, {})
        lines = [line for lines in data["sources_to_lines"].values() for line in lines]
        self.assertEqual(
            {line["move_out_id"] for line in lines},
            set((self.out_early.move_ids | self.out_late.move_ids).ids),
        )
        self.assertEqual(sum(1 for line in lines if line.get("is_extra")), 1)

    def test_assign_extra_line(self):
        data = self.report.get_report_data(self.receipt.ids, {})
        extra = next(
            line
            for lines in data["sources_to_lines"].values()
            for line in lines
            if line.get("is_extra")
        )
        self.report.action_assign(
            [extra["move_out_id"]], [extra["quantity"]], [extra["move_ins"]]
        )
        self.assertEqual(self.receipt.move_ids.move_dest_ids, self.out_late.move_ids)

    def _lines_by_out(self):
        data = self.report.get_report_data(self.receipt.ids, {})
        return {
            line["move_out_id"]: line
            for lines in data["sources_to_lines"].values()
            for line in lines
        }

    def _assign(self, line):
        self.report.action_assign(
            [line["move_out_id"]], [line["quantity"]], [line["move_ins"]]
        )

    def test_cannot_assign_same_stock_twice(self):
        lines = self._lines_by_out()
        early = lines[self.out_early.move_ids.id]
        late = lines[self.out_late.move_ids.id]
        self._assign(late)
        with self.assertRaises(UserError), self.cr.savepoint():
            self._assign(early)
        self.assertEqual(self.receipt.move_ids.move_dest_ids, self.out_late.move_ids)

    def test_repeated_assign_is_not_an_error(self):
        late = self._lines_by_out()[self.out_late.move_ids.id]
        self._assign(late)
        self._assign(late)
        self.assertEqual(self.receipt.move_ids.move_dest_ids, self.out_late.move_ids)

    def test_assign_all_within_available_is_allowed(self):
        lines = [
            line for line in self._lines_by_out().values() if not line.get("is_extra")
        ]
        self.report.action_assign(
            [line["move_out_id"] for line in lines],
            [line["quantity"] for line in lines],
            [line["move_ins"] for line in lines],
        )
        self.assertEqual(self.receipt.move_ids.move_dest_ids, self.out_early.move_ids)
