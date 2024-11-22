from odoo import models, fields, api
from odoo.tools import float_is_zero, float_compare


RECEIPT_STATES = [
    ("no", "No Receipts"),
    ("none", "All Outstanding"),
    ("partial", "Some Outstanding"),
    ("complete", "Fully Receipted"),
    ("overcompleted", "Over Receipted"),
]


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    receipt_status = fields.Selection(
        RECEIPT_STATES,
        default='no',
        store=True,
        readonly=True,
        compute='_compute_receipt_status'
    )

    @api.multi
    @api.depends('order_line.receipt_status', 'state')
    def _compute_receipt_status(self):
        for record in self:
            if record.state not in ("purchase", "done"):
                record.receipt_status = "no"
                continue

            line_receipt_status = (
                record
                .order_line
                .filtered(lambda l: l.state != 'cancel')
                .mapped('receipt_status')
            )

            if all(
                receipt_status == "none"
                for receipt_status in line_receipt_status
            ):
                record.receipt_status = "none"
                continue

            if any(
                receipt_status == "partial" for receipt_status in line_receipt_status
            ):
                record.receipt_status = "partial"
                continue

            if all(
                receipt_status == "complete"
                for receipt_status in line_receipt_status
            ):
                record.receipt_status = "complete"
                continue

            if any(
                receipt_status == "overcompleted"
                for receipt_status in line_receipt_status
            ):
                record.receipt_status = "overcompleted"
                continue

            record.receipt_status = "none"


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    receipt_status = fields.Selection(
        RECEIPT_STATES,
        default='no',
        store=True,
        readonly=True,
        compute='_compute_receipt_status'
    )

    @api.depends('qty_received', 'product_uom_qty', 'state')
    @api.multi
    def _compute_receipt_status(self):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        for record in self:
            if record.state not in ("purchase", "done"):
                record.receipt_status = "no"
                continue

            remaining = record.product_uom_qty - record.qty_received

            if remaining > 0 and float_compare(
                record.product_uom_qty,
                remaining,
                precision_digits=precision
            ) == 0:
                record.receipt_status = "none"
                continue

            if remaining > 0 and not float_is_zero(
                remaining, precision_digits=precision
            ):
                record.receipt_status = "partial"
                continue

            if remaining < 0 and not float_is_zero(
                remaining, precision_digits=precision
            ):
                record.receipt_status = "overcompleted"
                continue

            record.receipt_status = "complete"
