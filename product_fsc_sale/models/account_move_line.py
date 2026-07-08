from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Snapshot of the product's FSC claim, frozen when the line is created (or
    # carried over from the sale order line). Depends only on product_id so a
    # later reclassification never rewrites an already-issued invoice.
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
