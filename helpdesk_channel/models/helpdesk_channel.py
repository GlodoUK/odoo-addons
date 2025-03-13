from odoo import fields, models


class HelpdeskChannel(models.Model):
    _name = "helpdesk.channel"
    _description = "Helpdesk Channel"
    _order = "sequence asc, id"

    sequence = fields.Integer(default=20)
    name = fields.Char(required=True)
