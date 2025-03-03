from odoo.tests.common import TransactionCase


class CreditControlTestCase(TransactionCase):
    def setUp(self):
        super(CreditControlTestCase, self).setUp()

        self.partner_id = self.env["res.partner"].create({"name": "Test Customer"})

        self.pricelist_id = self.env["product.pricelist"].create(
            {
                "name": "GBP Test Price List",
                "active": True,
                "currency_id": self.env.ref("base.GBP").id,
                "company_id": self.env.user.company_id.id,
            }
        )

        prod_categ_all_id = self.env.ref("product.product_category_all")

        self.product1 = self.env["product.product"].create(
            {"name": "Product A", "categ_id": prod_categ_all_id.id}
        )

        self.product2 = self.env["product.product"].create(
            {
                "name": "Product A",
                "categ_id": prod_categ_all_id.id,
            }
        )

        self.classification_accounts = self.env["credit.control.classification"].create(
            {"name": "Accounts"}
        )
        self.classification_sales = self.env["credit.control.classification"].create(
            {"name": "Sales"}
        )
