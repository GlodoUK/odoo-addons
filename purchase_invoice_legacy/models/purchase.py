from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_create_invoice(self):
        if self.env.context.get("skip_purchase_invoice_legacy"):
            return super().action_create_invoice()

        moves = self.env["account.move"]
        for record in self:
            moves |= record._action_create_invoice_legacy_mode()
        return self.action_view_invoice(moves)

    def _action_create_invoice_legacy_mode(self):
        # 12.0 allowed you to effectively create an invoice at any time
        # This restores that functionality
        self.ensure_one()

        if self.state not in ("purchase", "draft"):
            raise UserError(_("Purchase order must be in 'purchase' or 'draft' state!"))

        self.env["decimal.precision"].precision_get("Product Unit of Measure")

        sequence = 10
        order = self.with_company(self.company_id)
        pending_section = None

        # Invoice values.
        invoice_vals = order._prepare_invoice()

        for line in order.order_line:
            if line.display_type == "line_section":
                pending_section = line
                continue

            if pending_section:
                line_vals = pending_section._prepare_account_move_line_legacy_mode()
                line_vals.update({"sequence": sequence})
                invoice_vals["invoice_line_ids"].append((0, 0, line_vals))
                sequence += 1
                pending_section = None

            line_vals = line._prepare_account_move_line_legacy_mode()
            line_vals.update({"sequence": sequence})
            invoice_vals["invoice_line_ids"].append((0, 0, line_vals))
            sequence += 1

        if not invoice_vals:
            raise UserError(
                _(
                    "There is no invoiceable line. If a product has a control"
                    " policy based on received quantity, please make sure that"
                    " a quantity has been received."
                )
            )

        return (
            self.env["account.move"]
            .with_context(default_move_type="in_invoice")
            .create(invoice_vals)
        )


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_account_move_line_legacy_mode(self, move=False):
        res = self._prepare_account_move_line(move)

        if not self.display_type and self.product_id and self.product_uom:
            # use 12.0 logic to determine the actual quantity
            if self.product_id.purchase_method == "purchase":
                qty = self.product_qty - self.qty_invoiced
            else:
                qty = self.qty_received - self.qty_invoiced
            if (
                float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding)
                <= 0
            ):
                qty = 0.0

            res.update({"quantity": qty})

        return res
