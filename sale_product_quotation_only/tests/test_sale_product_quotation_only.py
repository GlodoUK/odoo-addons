from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductGrey(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ResPartner = cls.env["res.partner"]
        cls.ProductProduct = cls.env["product.product"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.SaleOrderLine = cls.env["sale.order.line"]

        cls.partnerA = cls.ResPartner.create(
            {
                "name": "Partner",
            }
        )

        cls.productA = cls.ProductProduct.create(
            {
                "name": "Product Quotation Only",
            }
        )

        cls.orderA = cls.SaleOrder.create(
            {
                "partner_id": cls.partnerA.id,
            }
        )

    def test_action_confirm(self):
        self.SaleOrderLine.create(
            {
                "order_id": self.orderA.id,
                "product_id": self.productA.id,
            }
        )

        self.productA.quotation_only = True

        with self.assertRaises(UserError):
            self.orderA.action_confirm()

        self.productA.quotation_only = False

        self.orderA.action_confirm()

        self.assertEqual(
            self.orderA.state, "sale", "The sales order should be confirmed!"
        )

    def test_check_quotation_only_product(self):
        self.orderA.action_confirm()

        self.productA.quotation_only = True

        with self.assertRaises(ValidationError):
            self.SaleOrderLine.create(
                {
                    "order_id": self.orderA.id,
                    "product_id": self.productA.id,
                }
            )
