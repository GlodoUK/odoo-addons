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

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "categ_id": self.env.ref("product.product_category_all").id,
                "invoice_policy": "order",
            }
        )

        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "brand_id": self.env.ref("brands.other_brand").id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 1.00})
                ],
            }
        )

    def test_brand_id_propagation(self):
        self.sale_order.action_confirm()
        self.assertIn(
            self.sale_order.state, ["sale", "done"], "Sale Order Failed to Confirm"
        )

        invoice = self.sale_order._create_invoices()
        self.assertEqual(
            invoice.brand_id, self.sale_order.brand_id, "Brand ID Failed to Propagate"
        )
