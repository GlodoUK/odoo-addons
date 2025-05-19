from odoo import fields, models


class SpringService(models.Model):
    _name = "delivery.spring.service"
    _description = "Spring Service"

    active = fields.Boolean(default=True)
    name = fields.Char()
    ref = fields.Char()
