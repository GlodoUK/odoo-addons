from odoo.tests.common import TransactionCase


class TestPurchaseOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Partner A"})

        self.partner_invoicing = self.env["res.partner"].create(
            {
                "parent_id": self.partner.id,
                "name": "Accounts",
                "type": "invoice",
            }
        )

    def test_purchase_prepare_invoice(self):
        purchase_id = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )

        invoice_vals = purchase_id._prepare_invoice()

        self.assertEqual(
            invoice_vals.get("partner_id"),
            self.partner.id,
        )
