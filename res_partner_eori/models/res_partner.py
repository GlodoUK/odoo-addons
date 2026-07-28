from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    eori = fields.Char(
        "EORI",
        tracking=True,
    )

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ["eori"]
