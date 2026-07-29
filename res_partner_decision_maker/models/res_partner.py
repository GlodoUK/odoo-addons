from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    decision_maker_id = fields.Many2one("res.partner")
    decision_maker_email = fields.Char(
        related="decision_maker_id.email", string="Decision Maker Email"
    )
    decision_maker_function = fields.Char(
        related="decision_maker_id.function", string="Decision Maker Job Position"
    )
    decision_maker_phone = fields.Char(
        related="decision_maker_id.phone", string="Decision Maker Phone"
    )
