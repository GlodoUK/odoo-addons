from odoo import Command
from odoo.tests.common import TransactionCase


class TestForceDeliveredQuantity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.partner = cls.env["res.partner"].create({"name": "Force Delivered"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Force Delivered Product",
                "default_code": "TEST_SFDQ_PRODUCT",
                "type": "consu",
                "is_storable": True,
            }
        )

    def _order(self, quantity, forced):
        order = (
            self.env["sale.order"]
            .with_context(skip_delivery_auto=True)
            .create(
                {
                    "partner_id": self.partner.id,
                    "warehouse_id": self.warehouse.id,
                    "order_line": [
                        Command.create(
                            {
                                "product_id": self.product.id,
                                "product_uom_qty": quantity,
                            }
                        )
                    ],
                }
            )
        )
        # set on the existing line, as the import does: in create vals core's
        # qty_delivered default stands in for the compute
        order.order_line.force_delivered_quantity = forced
        return order, order.order_line

    def _live_moves(self, line):
        return line.move_ids.filtered(lambda move: move.state not in ("done", "cancel"))

    def test_forced_counts_as_delivered(self):
        _order, line = self._order(15, 10)
        self.assertEqual(line.qty_delivered_method, "stock_move")
        self.assertEqual(line.qty_delivered, 10)

    def test_confirm_procures_only_the_rest(self):
        order, line = self._order(15, 10)
        order.action_confirm()
        self.assertEqual(sum(self._live_moves(line).mapped("product_uom_qty")), 5)
        self.assertEqual(line.qty_delivered, 10)

    def test_delivering_the_rest_adds_on_top(self):
        order, line = self._order(15, 10)
        order.action_confirm()
        for move in self._live_moves(line):
            move.quantity = move.product_uom_qty
            move.picked = True
        order.picking_ids.with_context(skip_backorder=True).button_validate()
        self.assertEqual(line.qty_delivered, 15)

    def test_forced_in_full_procures_nothing(self):
        order, line = self._order(15, 15)
        order.action_confirm()
        self.assertFalse(self._live_moves(line))
        self.assertEqual(line.qty_delivered, 15)

    def test_raising_the_quantity_procures_only_the_increase(self):
        order, line = self._order(15, 15)
        order.action_confirm()
        order.action_unlock()
        line.product_uom_qty = 18
        self.assertEqual(sum(self._live_moves(line).mapped("product_uom_qty")), 3)
