from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Snapshot of the product's FSC claim, frozen when the line is created.
    # Depending only on product_id means reclassifying the product later does
    # not rewrite the claim printed on already-issued quotations/orders.
    fsc_label = fields.Char(
        string="FSC Claim",
        compute="_compute_fsc_label",
        store=True,
        readonly=False,
        copy=True,
    )

    @api.depends("product_id")
    def _compute_fsc_label(self):
        for line in self:
            product = line.product_id
            line.fsc_label = product.fsc_label if product.fsc_certified else False

    def _prepare_invoice_line(self, **optional_values):
        # Carry the order's frozen claim onto the invoice so the invoice states
        # what was actually sold, not the product's classification at invoicing.
        values = super()._prepare_invoice_line(**optional_values)
        values["fsc_label"] = self.fsc_label
        return values
