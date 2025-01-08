from odoo import fields, models


class FakeTestModel(models.Model):
    _name = "fake.test.model"
    _inherit = "mail.thread"
    _description = "Mail Partner Forwarding Test Model"

    partner_id = fields.Many2one("res.partner", required=True)
