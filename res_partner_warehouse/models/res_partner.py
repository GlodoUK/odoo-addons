from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_warehouse_ids = fields.One2many("res.partner.warehouse", "partner_id")
