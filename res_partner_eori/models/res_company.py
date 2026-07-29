from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    eori = fields.Char(
        related="partner_id.eori",
        string="EORI",
        readonly=False,
    )
