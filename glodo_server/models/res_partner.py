from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    glodo_instance_ids = fields.One2many("glodo.instance", "partner_id", readonly=True)
