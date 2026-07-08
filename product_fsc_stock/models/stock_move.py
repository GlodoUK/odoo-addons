from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # Snapshot of the product's FSC claim, frozen when the move is created.
    # Depending only on product_id means reclassifying the product later does
    # not rewrite the claim printed on already-issued delivery notes.
    fsc_label = fields.Char(
        string="FSC Claim",
        compute="_compute_fsc_label",
        store=True,
        readonly=False,
        copy=True,
    )

    @api.depends("product_id")
    def _compute_fsc_label(self):
        for move in self:
            product = move.product_id
            move.fsc_label = product.fsc_label if product.fsc_certified else False
