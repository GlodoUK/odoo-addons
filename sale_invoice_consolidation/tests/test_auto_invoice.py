from datetime import date

from freezegun import freeze_time

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleAutoInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Auto Invoice Co"})
        # Ordered-quantity policy so a confirmed order is immediately "to invoice".
        cls.product = cls.env["product.product"].create(
            {
                "name": "Auto Invoice Service",
                "type": "service",
                "invoice_policy": "order",
                "list_price": 100.0,
            }
        )

    def _confirmed_order(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        return order

    def _run_cron(self):
        self.env["res.partner"]._cron_auto_create_invoices()

    @freeze_time("2026-06-03")
    def test_advance_rolls_one_period(self):
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = date(2026, 6, 1)
        self.assertEqual(self.partner._sale_auto_invoice_advance(), date(2026, 7, 1))

    @freeze_time("2026-06-03")
    def test_advance_catches_up_missed_periods_in_one_jump(self):
        # Several periods overdue: must land on the next future grid point,
        # keeping the day-of-month anchor, not just +1 period.
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = date(2026, 1, 1)
        self.assertEqual(self.partner._sale_auto_invoice_advance(), date(2026, 7, 1))

    @freeze_time("2026-06-03")
    def test_advance_without_frequency_returns_false(self):
        self.partner.sale_auto_invoice_next_date = date(2026, 1, 1)
        self.assertFalse(self.partner._sale_auto_invoice_advance())

    @freeze_time("2026-06-03")
    def test_cron_invoices_due_consolidated(self):
        self.partner.sale_invoice_consolidation = "grouped"
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = date(2026, 5, 1)
        self._confirmed_order()
        self._confirmed_order()

        self._run_cron()

        invoices = self.env["account.move"].search(
            [
                ("partner_id", "=", self.partner.id),
                ("move_type", "=", "out_invoice"),
            ]
        )
        # Consolidated: the two orders merge into a single invoice.
        self.assertEqual(len(invoices), 1)
        # Date rolled forward onto the next future grid point.
        self.assertEqual(self.partner.sale_auto_invoice_next_date, date(2026, 7, 1))

    @freeze_time("2026-06-03")
    def test_cron_invoices_due_unconsolidated(self):
        self.partner.sale_invoice_consolidation = "ungrouped"
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = date(2026, 5, 1)
        self._confirmed_order()
        self._confirmed_order()

        self._run_cron()

        invoices = self.env["account.move"].search(
            [
                ("partner_id", "=", self.partner.id),
                ("move_type", "=", "out_invoice"),
            ]
        )
        # Consolidated: the two orders merge into a single invoice.
        self.assertEqual(len(invoices), 2)
        # Date rolled forward onto the next future grid point.
        self.assertEqual(self.partner.sale_auto_invoice_next_date, date(2026, 7, 1))

    @freeze_time("2026-06-03")
    def test_cron_skips_not_due(self):
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = date(2026, 12, 1)
        self._confirmed_order()

        self._run_cron()

        self.assertFalse(
            self.env["account.move"].search(
                [
                    ("partner_id", "=", self.partner.id),
                ]
            )
        )
        # Untouched.
        self.assertEqual(self.partner.sale_auto_invoice_next_date, date(2026, 12, 1))

    @freeze_time("2026-06-03")
    def test_cron_skips_when_disabled(self):
        # Due date passed but no frequency => auto-invoicing disabled.
        self.partner.sale_auto_invoice_next_date = date(2026, 1, 1)
        self._confirmed_order()

        self._run_cron()

        self.assertFalse(
            self.env["account.move"].search(
                [
                    ("partner_id", "=", self.partner.id),
                ]
            )
        )
