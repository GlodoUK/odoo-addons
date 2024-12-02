from odoo.tests import tagged

from odoo.addons.product_commingle.tests.common import CommonCommingleCase


@tagged("post_install", "-at_install")
class TestSale(CommonCommingleCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_bolta.type = "product"
        cls.product_boltb.type = "product"
        cls.product_bolt_equiv.type = "product"
        cls.product_bolt_equiv.commingled_policy = "strict"

        cls.stock_location = cls.env.ref("stock.stock_location_stock")

        cls.env["stock.quant"]._update_available_quantity(
            cls.product_boltb, cls.stock_location, 10
        )

        cls.env["stock.quant"]._update_available_quantity(
            cls.product_bolta, cls.stock_location, 5
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
            }
        )

    def test_commingled_no_split(self):
        sale_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_bolt_equiv.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )

        res = sale_id.order_line._onchange_product_id_commingle()
        self.assertFalse(res, "there should not be a warning when there is no split")

    def test_commingled_split(self):
        sale_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_bolt_equiv.id,
                            "product_uom_qty": 11,
                        },
                    )
                ],
            }
        )

        res = sale_id.order_line._onchange_product_id_commingle()
        self.assertTrue(res, "there should be a warning when there is a split")
