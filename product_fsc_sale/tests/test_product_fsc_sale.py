from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductFscSale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "FSC Board",
                "type": "consu",
                "invoice_policy": "order",
                "fsc_certified": True,
                "fsc_classification": "fsc_mix",
                "fsc_percentage": 0.7,
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.env["res.partner"].create({"name": "Customer"}).id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )

    def test_order_line_snapshot(self):
        line = self.order.order_line
        self.assertEqual(line.fsc_label, "FSC Mix 70%")
        self.product.fsc_classification = "fsc_recycled"
        self.assertEqual(line.fsc_label, "FSC Mix 70%")

    def test_invoice_uses_order_claim(self):
        self.order.action_confirm()
        self.product.fsc_classification = "fsc_recycled"
        invoice = self.order._create_invoices()
        self.assertEqual(invoice.invoice_line_ids.fsc_label, "FSC Mix 70%")

    def test_reports(self):
        self.order.action_confirm()
        invoice = self.order._create_invoices()
        report = self.env["ir.actions.report"]
        for report_ref, record in (
            ("sale.action_report_saleorder", self.order),
            ("account.account_invoices", invoice),
        ):
            html = report._render_qweb_html(report_ref, record.ids)[0].decode()
            self.assertIn("FSC Mix 70%", html)
