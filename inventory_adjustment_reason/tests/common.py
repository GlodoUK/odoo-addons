from odoo.tests.common import TransactionCase


class TestCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ProductProduct = cls.env["product.product"]
        cls.StockQuant = cls.env["stock.quant"]
        cls.StockMoveLine = cls.env["stock.move.line"]

        cls.productA = cls.ProductProduct.create({
            "name": "Product A",
            "type": "product",
        })
