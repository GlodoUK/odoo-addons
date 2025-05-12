from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestBrandIdPropagation(AccountTestInvoicingCommon):
    def setUp(self):
        super().setUp()

        self.partner_id = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        self.product_id = self.env["product.product"].create(
            {
                "name": "Test Product",
            }
        )

        self.order_id = self.env["sale.order"].create(
            {
                "brand_id": self.env.ref("brands.other_brand").id,
                "partner_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )

    def test_brand_id_propagation(self):
        self.order_id.action_confirm()

        self.assertIn(
            self.order_id.state, ["sale", "done"], "The sales order failed to confirm!"
        )

        move_id = self.order_id._create_invoices()

        self.assertEqual(
            move_id.brand_id,
            self.order_id.brand_id,
            "The brand failed to propagate to the invoice!",
        )
