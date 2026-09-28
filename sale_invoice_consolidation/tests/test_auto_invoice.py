from datetime import datetime

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

    def _confirmed_order(self, qty=1):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        return order

    def _credit_pending_order(self):
        """
        Return an order whose pending quantity is negative.

        Invoiced in full, then reduced: the only thing left to raise for it is a
        credit note, which Odoo only does when invoiced with ``final``.
        """
        order = self._confirmed_order(qty=2)
        order._create_invoices()
        order.order_line.product_uom_qty = 1
        self.assertEqual(order.order_line.qty_to_invoice, -1)
        self.assertEqual(order.invoice_status, "to invoice")
        return order

    def _run_cron(self):
        self.env["res.partner"]._cron_auto_create_invoices()

    def _partner_moves(self):
        return self.env["account.move"].search([("partner_id", "=", self.partner.id)])

    @freeze_time("2026-06-03")
    def test_advance_rolls_one_period(self):
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 6, 1)
        self.assertEqual(
            self.partner._sale_auto_invoice_advance(), datetime(2026, 7, 1)
        )

    @freeze_time("2026-06-03")
    def test_advance_catches_up_missed_periods_in_one_jump(self):
        # Several periods overdue: must land on the next future grid point,
        # keeping the day-of-month anchor, not just +1 period.
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 1, 1)
        self.assertEqual(
            self.partner._sale_auto_invoice_advance(), datetime(2026, 7, 1)
        )

    @freeze_time("2026-06-24 09:30:00")
    def test_advance_hourly_rolls_one_hour(self):
        # Sub-day cadence: the grid anchor (minute past the hour) is preserved
        # and the value advances by whole hours - impossible on a date field.
        self.partner.sale_auto_invoice_frequency = "hourly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 6, 24, 9, 0, 0)
        self.assertEqual(
            self.partner._sale_auto_invoice_advance(),
            datetime(2026, 6, 24, 10, 0, 0),
        )

    @freeze_time("2026-06-24 09:30:00")
    def test_advance_hourly_catches_up_missed_hours_in_one_jump(self):
        self.partner.sale_auto_invoice_frequency = "hourly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 6, 24, 3, 0, 0)
        self.assertEqual(
            self.partner._sale_auto_invoice_advance(),
            datetime(2026, 6, 24, 10, 0, 0),
        )

    @freeze_time("2026-06-03")
    def test_advance_without_frequency_returns_false(self):
        self.partner.sale_auto_invoice_next_date = datetime(2026, 1, 1)
        self.assertFalse(self.partner._sale_auto_invoice_advance())

    @freeze_time("2026-06-03")
    def test_cron_invoices_due_consolidated(self):
        self.partner.sale_invoice_consolidation = "grouped"
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 5, 1)
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
        # Rolled forward onto the next future grid point.
        self.assertEqual(self.partner.sale_auto_invoice_next_date, datetime(2026, 7, 1))

    @freeze_time("2026-06-03")
    def test_cron_invoices_due_unconsolidated(self):
        self.partner.sale_invoice_consolidation = "ungrouped"
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 5, 1)
        self._confirmed_order()
        self._confirmed_order()

        self._run_cron()

        invoices = self.env["account.move"].search(
            [
                ("partner_id", "=", self.partner.id),
                ("move_type", "=", "out_invoice"),
            ]
        )
        # Individual: one invoice per order.
        self.assertEqual(len(invoices), 2)
        # Rolled forward onto the next future grid point.
        self.assertEqual(self.partner.sale_auto_invoice_next_date, datetime(2026, 7, 1))

    @freeze_time("2026-06-24 09:30:00")
    def test_cron_invoices_due_hourly(self):
        self.partner.sale_invoice_consolidation = "grouped"
        self.partner.sale_auto_invoice_frequency = "hourly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 6, 24, 8, 0, 0)
        self._confirmed_order()

        self._run_cron()

        invoices = self.env["account.move"].search(
            [
                ("partner_id", "=", self.partner.id),
                ("move_type", "=", "out_invoice"),
            ]
        )
        self.assertEqual(len(invoices), 1)
        # Rolled forward to the next future hour on the same minute grid.
        self.assertEqual(
            self.partner.sale_auto_invoice_next_date,
            datetime(2026, 6, 24, 10, 0, 0),
        )

    @freeze_time("2026-06-03")
    def test_cron_skips_not_due(self):
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 12, 1)
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
        self.assertEqual(
            self.partner.sale_auto_invoice_next_date, datetime(2026, 12, 1)
        )

    @freeze_time("2026-06-03")
    def test_cron_raises_credit_note_when_company_allows_it(self):
        self.env.company.sale_auto_invoice_credit_notes = True
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 5, 1)
        order = self._credit_pending_order()
        before = self._partner_moves()

        self._run_cron()

        created = self._partner_moves() - before
        self.assertEqual(created.mapped("move_type"), ["out_refund"])
        self.assertEqual(order.invoice_status, "invoiced")
        self.assertEqual(self.partner.sale_auto_invoice_next_date, datetime(2026, 7, 1))

    @freeze_time("2026-06-03")
    def test_cron_skips_credit_note_when_company_disallows_it(self):
        self.env.company.sale_auto_invoice_credit_notes = False
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 5, 1)
        order = self._credit_pending_order()
        before = self._partner_moves()

        self._run_cron()

        self.assertFalse(self._partner_moves() - before)
        # Left pending, to be credited by hand.
        self.assertEqual(order.invoice_status, "to invoice")
        # The schedule still rolls forward: an order the run cannot invoice must
        # not stall the customer's cadence.
        self.assertEqual(self.partner.sale_auto_invoice_next_date, datetime(2026, 7, 1))

    @freeze_time("2026-06-03")
    def test_cron_still_invoices_positive_orders_when_credit_notes_disallowed(self):
        # Turning credit notes off must only drop the orders that need one.
        self.env.company.sale_auto_invoice_credit_notes = False
        self.partner.sale_invoice_consolidation = "grouped"
        self.partner.sale_auto_invoice_frequency = "monthly"
        self.partner.sale_auto_invoice_next_date = datetime(2026, 5, 1)
        credit_order = self._credit_pending_order()
        self._confirmed_order()
        before = self._partner_moves()

        self._run_cron()

        created = self._partner_moves() - before
        self.assertEqual(created.mapped("move_type"), ["out_invoice"])
        # Only the positive order made it onto the invoice.
        self.assertEqual(created.invoice_line_ids.quantity, 1)
        self.assertEqual(credit_order.invoice_status, "to invoice")

    @freeze_time("2026-06-03")
    def test_cron_skips_when_disabled(self):
        # Due moment passed but no frequency => auto-invoicing disabled.
        self.partner.sale_auto_invoice_next_date = datetime(2026, 1, 1)
        self._confirmed_order()

        self._run_cron()

        self.assertFalse(
            self.env["account.move"].search(
                [
                    ("partner_id", "=", self.partner.id),
                ]
            )
        )

    def test_order_mirrors_partner_auto_invoice_setting(self):
        order = self._confirmed_order()
        self.assertFalse(order.sale_auto_invoice_enabled)

        self.partner.sale_auto_invoice_frequency = "monthly"
        self.assertTrue(order.sale_auto_invoice_enabled)

        self.partner.sale_auto_invoice_frequency = False
        self.assertFalse(order.sale_auto_invoice_enabled)

    def test_order_mirrors_invoice_address_not_commercial_entity(self):
        # Same contract as the cron: the setting is read from the invoice
        # address itself, not inherited from the customer it belongs to.
        invoice_contact = self.env["res.partner"].create(
            {
                "name": "Auto Invoice Billing",
                "type": "invoice",
                "parent_id": self.partner.id,
            }
        )
        order = self._confirmed_order()
        self.assertEqual(order.partner_invoice_id, invoice_contact)
        self.assertFalse(order.sale_auto_invoice_enabled)

        invoice_contact.sale_auto_invoice_frequency = "weekly"
        self.assertTrue(order.sale_auto_invoice_enabled)

        invoice_contact.sale_auto_invoice_frequency = False
        self.partner.sale_auto_invoice_frequency = "weekly"
        self.assertFalse(order.sale_auto_invoice_enabled)
