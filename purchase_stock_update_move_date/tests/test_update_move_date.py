from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestUpdateMoveDate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_id = cls.env["res.partner"].create({"name": "Example"})

        cls.product_id = cls.env["product.product"].create(
            {"name": "Product", "type": "product"}
        )

        cls.order_id = cls.env["purchase.order"].create(
            {"partner_id": cls.partner_id.id}
        )

        cls.order_line_id = cls.env["purchase.order.line"].create(
            {
                "order_id": cls.order_id.id,
                "product_id": cls.product_id.id,
            }
        )

    def test_update_move_date(self):
        self.order_id.button_confirm()

        self.assertEqual(
            self.order_id.picking_ids.move_ids.date,
            fields.Datetime.now(),
        )

        self.order_line_id.write(
            {"date_planned": fields.Datetime.now() + relativedelta(days=5)}
        )

        self.assertEqual(
            self.order_id.picking_ids.move_ids.date,
            fields.Datetime.now() + relativedelta(days=5),
        )
