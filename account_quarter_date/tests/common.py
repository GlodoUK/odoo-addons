from datetime import datetime

from odoo.tests.common import TransactionCase


class TestCommon(TransactionCase):
    def setUp(self):
        super(TestCommon, self).setUp()
        self.partner_id = self.env["res.partner"].create({"name": "Test Customer"})
        self.product1 = self.env["product.product"].create({"name": "Product A"})
        self.model_sale_order = self.env["sale.order"]
        self.model_sale_order_line = self.env["sale.order.line"]
        self.model_account_move = self.env["account.move"]
        self.previous_year = datetime.now().year - 1
