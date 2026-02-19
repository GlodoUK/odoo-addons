from odoo.fields import Command
from odoo.tests import tagged

from .common import TestCpqSaleMrpCommon


@tagged("post_install", "-at_install")
class TestGetCogsValue(TestCpqSaleMrpCommon):
    def _add_stock(self, product, qty, location=None):
        """Add inventory for a product at the given location."""
        if not location:
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", self.env.company.id)], limit=1
            )
            location = warehouse.lot_stock_id
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": product.id,
                "inventory_quantity": qty,
                "location_id": location.id,
            }
        ).action_apply_inventory()

    def test_cogs_value_cable_kit_100m(self):
        """COGS for a 100m Cable Loom Kit should equal the sum of component
        costs: (100 * 2) + (2 * 0) + (2 * 10) + (2 * 5) = 230."""

        # Ensure stock so delivery can be validated.
        self._add_stock(self.bulk_cable, 200)
        self._add_stock(self.rj45, 10)
        self._add_stock(self.boot, 10)
        self._add_stock(self.tie, 10)

        # Create a configured Cable Loom Kit variant: Black, 100m.
        variant = self.cable_kit_tmpl._cpq_get_create_variant(
            self.ptav_custom_length | self.ptav_black,
            {self.ptav_custom_length: 100.0},
        )

        # Create and confirm a Sale Order.
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": variant.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 500.0,
                            "tax_ids": False,
                        }
                    ),
                ],
            }
        )
        so.action_confirm()

        # The phantom kit should have exploded into component moves.
        picking = so.picking_ids
        self.assertTrue(picking, "Expected a delivery picking after SO confirmation")
        self.assertTrue(
            picking.move_ids.mapped("cpq_bom_id"),
            "Component moves must carry cpq_bom_id",
        )

        # Validate the delivery.
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.button_validate()

        self.assertEqual(picking.state, "done")

        # Create and post the invoice.
        invoice = so._create_invoices()
        invoice.action_post()

        # Find the COGS lines.
        cogs_lines = invoice.line_ids.filtered(lambda cl: cl.display_type == "cogs")
        self.assertTrue(cogs_lines, "Expected COGS lines on the posted invoice")

        # The expense-side COGS line has a positive debit.
        cogs_expense = cogs_lines.filtered(lambda cl: cl.debit > 0)
        self.assertTrue(cogs_expense, "Expected a COGS expense line with debit > 0")

        # Expected COGS:
        # Bulk Cat6 Cable: 100m * 2.0/m = 200.0
        # RJ45 Connector:  2   * 0.0    =   0.0
        # Strain Relief:   2   * 10.0   =  20.0
        # Velcro Tie:      2   * 5.0    =  10.0
        # Total                         = 230.0
        expected_cogs = 230.0
        self.assertEqual(
            cogs_expense.debit,
            expected_cogs,
            msg="COGS debit should equal the sum of component standard costs",
        )
