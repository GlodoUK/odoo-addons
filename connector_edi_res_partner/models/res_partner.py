from odoo import api, fields, models
from odoo.osv import expression


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "edi.message.mixin"]

    edi_partner_ids = fields.One2many(
        "edi.res.partner",
        "odoo_id",
        copy=False,
        string="EDI Contact Bindings",
    )

    edi_partner_count = fields.Integer(compute="_compute_edi_partner_count", store=True)

    @api.depends("edi_partner_ids")
    def _compute_edi_partner_count(self):
        for record in self:
            record.edi_partner_count = len(record.edi_partner_ids)

    def _edi_message_ids_domain(self):
        return expression.OR(
            [
                super()._edi_message_ids_domain(),
                [
                    ("model", "=", "edi.res.partner"),
                    ("res_id", "in", self.edi_partner_ids.ids),
                ],
            ]
        )
