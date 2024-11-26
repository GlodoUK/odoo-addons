from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env["res.partner"].create({"name": "Supplier Partner A"})
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Test Receiving Product A",
                "purchase_method": "receive",
                "type": "consu",
            }
        )

    def test_received_prepare_account_move_line_legacy_mode(self):
        purchase_id = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "product_qty": 10,
                        },
                    )
                ],
            }
        )

        purchase_id.button_confirm()

        vals = purchase_id.order_line._prepare_account_move_line_legacy_mode()
        self.assertEqual(vals.get("quantity", 0.0), 0.0)

        purchase_id.order_line.qty_received_method = "manual"
        purchase_id.order_line.qty_received_manual = 5

        vals = purchase_id.order_line._prepare_account_move_line_legacy_mode()
        self.assertEqual(vals.get("quantity", 0.0), 5.0)

        purchase_id.order_line.qty_received_method = "manual"
        purchase_id.order_line.qty_received_manual = 10

        vals = purchase_id.order_line._prepare_account_move_line_legacy_mode()
        self.assertEqual(vals.get("quantity", 0.0), 10.0)

    def test_received_real_invoice(self):
        purchase_id = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "product_qty": 10,
                        },
                    )
                ],
            }
        )

        purchase_id.button_confirm()
        move = purchase_id._action_create_invoice_legacy_mode()
        move.invoice_line_ids.quantity = 5

        vals = purchase_id.order_line._prepare_account_move_line_legacy_mode()
        self.assertEqual(vals.get("quantity", 0.0), 0.0)

        purchase_id.order_line.qty_received_method = "manual"
        purchase_id.order_line.qty_received_manual = 10
        vals = purchase_id.order_line._prepare_account_move_line_legacy_mode()
        self.assertEqual(vals.get("quantity", 0.0), 5.0)
