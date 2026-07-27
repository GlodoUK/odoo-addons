from odoo import fields, models


class GatekeeperTrigger(models.Model):
    _name = "gatekeeper.trigger"
    _description = "Gatekeeper Trigger"

    name = fields.Char(
        required=True,
    )
    action = fields.Char()
    model_name = fields.Char()
