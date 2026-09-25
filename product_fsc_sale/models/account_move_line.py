from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Snapshot: only depends on product_id, so issued documents never change.
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
