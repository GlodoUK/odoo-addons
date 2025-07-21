from datetime import datetime

from odoo.tests import tagged

from .common import TestCommon


@tagged("post_install", "-at_install")
class TestInventoryAdjustmentNote(TestCommon):
    def test_inventory_adjustment_note(self):
        quantA = self.StockQuant.create(
            {
                "inventory_date": datetime.now(),
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "note": "This is a test note",
                "product_id": self.product1.id,
                "inventory_quantity": 1,
            }
        )

        quantA.action_apply_inventory()

        move = self.model_stock_move_line.search(
            [
                ("product_id", "=", self.product1.id),
                ("note", "=", "This is a test note"),
            ]
        )
        self.assertEqual(move.note, "This is a test note")
