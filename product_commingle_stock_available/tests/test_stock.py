from odoo.tests import tagged

from odoo.addons.product_commingle.tests.common import CommonCommingleCase


@tagged("post_install", "-at_install")
class TestStock(CommonCommingleCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product_bolta.type = "product"
        cls.product_boltb.type = "product"
        cls.product_bolt_equiv.type = "product"
        cls.product_bolt_equiv.commingled_policy = "strict"

        cls.stock_location = cls.env.ref("stock.stock_location_stock")

    def test_commingled_no_stock(self):
        self.assertEqual(self.product_bolt_equiv.potential_qty, 0)
        self.assertEqual(self.product_bolt_equiv.immediately_usable_qty, 0)

    def test_commingled_partial_stock(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product_boltb, self.stock_location, 100
        )

        self.env["stock.quant"]._update_available_quantity(
            self.product_bolta, self.stock_location, 500
        )

        self.assertEqual(self.product_bolt_equiv.potential_qty, 600)
        self.assertEqual(self.product_bolt_equiv.immediately_usable_qty, 600)
