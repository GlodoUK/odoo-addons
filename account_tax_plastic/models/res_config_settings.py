from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    plastic_tax_basis = fields.Selection(
        related="company_id.plastic_tax_basis",
        readonly=False,
    )
    plastic_tax_rate = fields.Monetary(
        related="company_id.plastic_tax_rate",
        currency_field="plastic_tax_currency_id",
        readonly=False,
    )
    plastic_tax_currency_id = fields.Many2one(
        related="company_id.plastic_tax_currency_id",
        readonly=False,
    )
