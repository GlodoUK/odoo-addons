from odoo import fields, models


class MailMessage(models.Model):
    _inherit = "mail.message"

    glo_analytic_line_id = fields.Many2one(
        comodel_name="account.analytic.line",
        string="Analytic line",
        ondelete="set null",
    )
