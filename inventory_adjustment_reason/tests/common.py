from odoo.tests.common import TransactionCase


class TestCommon(TransactionCase):
    def setUp(self):
        super(TestCommon, self).setUp()
        self.product1 = self.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        self.model_stock_quant = self.env["stock.quant"]
        self.model_stock_move_line = self.env["stock.move.line"]
