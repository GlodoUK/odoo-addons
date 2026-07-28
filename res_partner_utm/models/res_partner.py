from odoo import fields, models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "utm.mixin"]

    # UTMs - enforcing the fact that we want to 'set null' when relation is unlinked
    campaign_id = fields.Many2one(ondelete="set null")
    medium_id = fields.Many2one(ondelete="set null")
    source_id = fields.Many2one(ondelete="set null")
