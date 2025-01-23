from datetime import datetime

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestUpdateMoveDate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_id = cls.env["res.partner"].create(
            {
                "name": "Example",
            }
        )

        cls.product_id = cls.env["product.product"].create(
            {
                "name": "Product",
                "type": "product",
            }
        )

    @freeze_time("2025-01-01 06:00:00")
    def test_update_move_date_order(self):
        order_id = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_id.id,
            }
        )

        self.env["purchase.order.line"].create(
            {
                "order_id": order_id.id,
                "product_id": self.product_id.id,
            }
        )

        order_id.button_confirm()

        self.assertEqual(
            order_id.picking_ids.move_ids.date,
            datetime(2025, 1, 1, 6, 0, 0),  # 6AM 2025 1st Jan
        )

        with Form(order_id) as form:
            date_planned_initial = order_id.date_planned
            form.date_planned = date_planned_initial + relativedelta(days=5)
            form.save()

        self.assertEqual(
            order_id.picking_ids.move_ids.date,
            datetime(2025, 1, 6, 6, 0, 0),  # 6AM 2025 6st Jan
        )

    @freeze_time("2025-01-01 06:00:00")
    def test_update_move_date_order_line(self):
        order_id = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_id.id,
            }
        )

        order_line_id = self.env["purchase.order.line"].create(
            {
                "order_id": order_id.id,
                "product_id": self.product_id.id,
            }
        )

        order_id.button_confirm()

        self.assertEqual(
            order_id.picking_ids.move_ids.date,
            datetime(2025, 1, 1, 6, 0, 0),  # 6AM 2025 1st Jan
        )

        date_planned_initial = order_line_id.date_planned

        order_line_id.write(
            {"date_planned": date_planned_initial + relativedelta(days=5)}
        )

        self.assertEqual(
            order_id.picking_ids.move_ids.date,
            datetime(2025, 1, 6, 6, 0, 0),  # 6AM 2025 6th Jan
        )