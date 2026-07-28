from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMov(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company_currency = cls.company.currency_id

        # A currency of our own, so that no pre-existing rate in the database
        # can interfere with the conversion assertions below.
        Currency = cls.env["res.currency"]
        cls.foreign_currency = Currency.with_context(active_test=False).search(
            [("name", "=", "XMV")], limit=1
        )
        if not cls.foreign_currency:
            cls.foreign_currency = Currency.create(
                {"name": "XMV", "symbol": "X", "rounding": 0.01}
            )
        cls.foreign_currency.active = True
        cls.foreign_currency.rate_ids.unlink()
        cls.env["res.currency.rate"].create(
            {
                "currency_id": cls.foreign_currency.id,
                "company_id": cls.company.id,
                "name": "2000-01-01",
                "rate": 2.0,
            }
        )

        cls.vendor = cls.env["res.partner"].create({"name": "MOV Vendor"})

        # The dev database is a copy of production, so anchor the fixture on a
        # default_code that cannot collide with the live catalogue.
        cls.product = cls.env["product.product"].create(
            {
                "name": "MOV Product",
                "default_code": "TEST-PURCHASE-MOV-01",
                "purchase_ok": True,
            }
        )

    def _make_po(self, *, price, currency=None, force_mov=False, partner=None):
        """Create a one-line draft purchase order worth ``price`` untaxed."""
        po = self.env["purchase.order"].create(
            {
                "partner_id": (partner or self.vendor).id,
                "force_mov": force_mov,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "price_unit": price,
                        }
                    )
                ],
            }
        )
        # currency_id is a precomputed stored field, so assign it after create
        # rather than through the create values.
        if currency and po.currency_id != currency:
            po.currency_id = currency
        return po

    def test_mov_defaults_to_zero(self):
        """property_purchase_mov defaults to 0 - i.e. no minimum."""
        self.assertEqual(self.vendor.property_purchase_mov, 0.0)

    def test_mov_currency_falls_back_to_company_currency(self):
        """With no Supplier Currency the MOV is read in the company currency."""
        self.assertFalse(self.vendor.property_purchase_currency_id)
        self.assertEqual(self.vendor.purchase_mov_currency_id, self.company_currency)

    def test_mov_currency_follows_supplier_currency(self):
        """With a Supplier Currency set, the MOV is read in that currency."""
        self.vendor.property_purchase_currency_id = self.foreign_currency
        self.assertEqual(self.vendor.purchase_mov_currency_id, self.foreign_currency)

    def test_zero_mov_no_check(self):
        """A vendor with no MOV imposes no minimum."""
        po = self._make_po(price=1.0)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_below_mov_raises(self):
        """Confirming below the MOV raises a ValidationError."""
        self.vendor.property_purchase_mov = 100.0
        po = self._make_po(price=50.0)
        self.assertEqual(po.currency_id, self.company_currency)
        with self.assertRaises(ValidationError):
            po.button_confirm()
        self.assertEqual(po.state, "draft")

    def test_exactly_mov_confirms(self):
        """An order worth exactly the MOV is allowed."""
        self.vendor.property_purchase_mov = 100.0
        po = self._make_po(price=100.0)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_above_mov_confirms(self):
        """An order above the MOV is allowed."""
        self.vendor.property_purchase_mov = 100.0
        po = self._make_po(price=250.0)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_force_mov_bypasses_check(self):
        """force_mov on the order skips the check even below the MOV."""
        self.vendor.property_purchase_mov = 100.0
        po = self._make_po(price=1.0, force_mov=True)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_mov_converted_from_company_currency(self):
        """No Supplier Currency: the MOV is converted into the order currency.

        The MOV is held in the company currency, the order is in XMV, so the
        threshold the order is measured against is the converted amount.
        """
        self.vendor.property_purchase_mov = 100.0
        po = self._make_po(price=1.0, currency=self.foreign_currency)
        self.assertEqual(po.currency_id, self.foreign_currency)

        expected = self.company_currency._convert(
            100.0, self.foreign_currency, self.company, po.date_order.date()
        )
        self.assertGreater(expected, 0.0)
        self.assertEqual(po._get_mov(), expected)
        # Sanity: the conversion must actually move the number, otherwise this
        # test would pass for the wrong reason.
        self.assertNotEqual(expected, 100.0)

        below = self._make_po(price=expected * 0.5, currency=self.foreign_currency)
        with self.assertRaises(ValidationError):
            below.button_confirm()

        above = self._make_po(price=expected * 1.5, currency=self.foreign_currency)
        above.button_confirm()
        self.assertEqual(above.state, "purchase")

    def test_mov_in_supplier_currency_is_not_converted(self):
        """Supplier Currency == order currency: the MOV is taken as-is."""
        self.vendor.property_purchase_currency_id = self.foreign_currency
        self.vendor.property_purchase_mov = 100.0

        po = self._make_po(price=99.0)
        self.assertEqual(po.currency_id, self.foreign_currency)
        self.assertEqual(po._get_mov(), 100.0)
        with self.assertRaises(ValidationError):
            po.button_confirm()

    def test_mov_converted_from_supplier_currency(self):
        """Supplier Currency != order currency: the MOV is converted."""
        self.vendor.property_purchase_currency_id = self.foreign_currency
        self.vendor.property_purchase_mov = 100.0

        po = self._make_po(price=1.0, currency=self.company_currency)
        self.assertEqual(po.currency_id, self.company_currency)

        expected = self.foreign_currency._convert(
            100.0, self.company_currency, self.company, po.date_order.date()
        )
        self.assertEqual(po._get_mov(), expected)

    def test_check_skips_non_draft_orders(self):
        """button_confirm only validates draft/sent orders."""
        self.vendor.property_purchase_mov = 100.0
        po = self._make_po(price=1.0, force_mov=True)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")
        # Re-confirming an order that has left draft/sent must not re-trigger
        # the check.
        po.force_mov = False
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_error_message_is_well_formed(self):
        """The ValidationError message builds without attribute errors."""
        self.vendor.property_purchase_mov = 100.0
        po = self._make_po(price=50.0)
        with self.assertRaises(ValidationError) as cm:
            po._check_mov()
        message = str(cm.exception)
        self.assertIn("minimum order value", message)
        self.assertIn(self.vendor.name, message)
