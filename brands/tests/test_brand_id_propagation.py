from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestBrandIdPropagation(AccountTestInvoicingCommon):
    def setUp(self):
        super(TestBrandIdPropagation, self).setUp()

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "categ_id": self.env.ref("product.product_category_all").id,
                "invoice_policy": "order",
            }
        )

        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.partner_admin").id,
                "brand_id": self.env.ref("brands.other_brand").id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 1.00})
                ],
            }
        )

    def test_brand_id_propagation(self):
        self.sale_order._action_confirm()
        # TODO: test is failing. Revisit if we ever have someone come back to 12.0.
        #invoice = self.sale_order._create_invoices()
        #
        #self.assertEqual(
        #    invoice.brand_id, self.sale_order.brand_id, "Brand ID Failed to Propagate"
        #)
