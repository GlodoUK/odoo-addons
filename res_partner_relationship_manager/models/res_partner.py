from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    relationship_manager_user_id = fields.Many2one(
        "res.users",
        "Relationship Manager",
        domain=[("share", "=", False)],
    )

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ["relationship_manager_user_id"]
