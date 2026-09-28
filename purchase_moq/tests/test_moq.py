from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMoq(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_pack_6 = cls.env.ref("uom.product_uom_pack_6")

        cls.vendor = cls.env["res.partner"].create({"name": "MOQ Vendor"})
        cls.other_vendor = cls.env["res.partner"].create({"name": "Other Vendor"})

    def _make_product(self, moq, *, min_qty=0.0, seller_uom=None, partner=None):
        """Create a product with a single seller carrying the given ``moq``."""
        return self.env["product.product"].create(
            {
                "name": "MOQ Product",
                "seller_ids": [
                    Command.create(
                        {
                            "partner_id": (partner or self.vendor).id,
                            "min_qty": min_qty,
                            "moq": moq,
                            "price": 10.0,
                            **({"product_uom_id": seller_uom.id} if seller_uom else {}),
                        }
                    )
                ],
            }
        )

    def _make_po(self, product, qty, *, uom=None, force_moq=False, partner=None):
        """Create a one-line draft purchase order."""
        return self.env["purchase.order"].create(
            {
                "partner_id": (partner or self.vendor).id,
                "force_moq": force_moq,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_qty": qty,
                            **({"product_uom_id": uom.id} if uom else {}),
                        }
                    )
                ],
            }
        )

    def test_moq_field_default_zero(self):
        """The moq field defaults to 0."""
        product = self.env["product.product"].create(
            {
                "name": "No MOQ Product",
                "seller_ids": [
                    Command.create({"partner_id": self.vendor.id, "price": 1.0})
                ],
            }
        )
        self.assertEqual(product.seller_ids.moq, 0.0)

    def test_below_moq_raises(self):
        """Confirming below the MOQ raises a ValidationError."""
        product = self._make_product(moq=10)
        po = self._make_po(product, qty=5)
        # Sanity: the seller must actually be selected, otherwise the check
        # would be skipped for an unrelated reason.
        self.assertEqual(po.order_line.selected_seller_id.moq, 10)
        with self.assertRaises(ValidationError):
            po.button_confirm()
        self.assertEqual(po.state, "draft")

    def test_exactly_moq_confirms(self):
        """Ordering exactly the MOQ is allowed."""
        product = self._make_product(moq=10)
        po = self._make_po(product, qty=10)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_above_moq_confirms(self):
        """Ordering above the MOQ is allowed."""
        product = self._make_product(moq=10)
        po = self._make_po(product, qty=25)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_zero_moq_no_check(self):
        """A seller with moq=0 imposes no minimum."""
        product = self._make_product(moq=0)
        po = self._make_po(product, qty=1)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_force_moq_bypasses_check(self):
        """force_moq on the order skips the check even below the MOQ."""
        product = self._make_product(moq=10)
        po = self._make_po(product, qty=1, force_moq=True)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_no_seller_skips_check(self):
        """A line whose vendor has no matching seller is not checked."""
        product = self._make_product(moq=10)
        # Order from a different vendor: no supplierinfo matches, so
        # selected_seller_id is empty and the line is skipped.
        po = self._make_po(product, qty=1, partner=self.other_vendor)
        self.assertFalse(po.order_line.selected_seller_id)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_moq_respects_uom_conversion_below(self):
        """The line qty is converted to the seller's UoM before comparison.

        Seller MOQ is 12 Units. Ordering 1 Pack of 6 == 6 Units < 12 -> raise.
        """
        product = self._make_product(moq=12, seller_uom=self.uom_unit)
        po = self._make_po(product, qty=1, uom=self.uom_pack_6)
        self.assertEqual(po.order_line.selected_seller_id.moq, 12)
        with self.assertRaises(ValidationError):
            po.button_confirm()

    def test_moq_respects_uom_conversion_at(self):
        """2 Packs of 6 == 12 Units == MOQ -> allowed."""
        product = self._make_product(moq=12, seller_uom=self.uom_unit)
        po = self._make_po(product, qty=2, uom=self.uom_pack_6)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_check_skips_non_draft_orders(self):
        """button_confirm only validates draft/sent orders."""
        product = self._make_product(moq=10)
        po = self._make_po(product, qty=1, force_moq=True)
        po.button_confirm()
        self.assertEqual(po.state, "purchase")
        # Re-confirming a purchase-state order must not re-trigger the MOQ
        # check (the order is no longer draft/sent).
        po.force_moq = False
        po.button_confirm()
        self.assertEqual(po.state, "purchase")

    def test_error_message_is_well_formed(self):
        """The ValidationError message builds without attribute errors."""
        product = self._make_product(moq=10, seller_uom=self.uom_unit)
        po = self._make_po(product, qty=5)
        with self.assertRaises(ValidationError) as cm:
            po.order_line._check_moq()
        message = str(cm.exception)
        self.assertIn("minimum quantity", message)
        self.assertIn(self.vendor.name, message)
        self.assertIn(product.name, message)
