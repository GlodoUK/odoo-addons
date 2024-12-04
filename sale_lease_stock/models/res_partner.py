from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    lease_ok = fields.Boolean(
        default=True,
        string="Can Lease",
    )
    sale_ok = fields.Boolean(
        default=True,
        string="Can Outright Purchase",
    )

    @api.model
    def _commercial_fields(self):
        res = super(ResPartner, self)._commercial_fields()
        res += ["lease_ok", "sale_ok"]
        return res
