from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_auto_invoice_credit_notes = fields.Boolean(
        related="company_id.sale_auto_invoice_credit_notes",
        readonly=False,
    )
