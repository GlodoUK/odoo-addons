from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    plastic_tax_basis = fields.Selection(
        [("net_weight", "Net Weight"), ("gross_weight", "Gross Weight")],
        default="net_weight",
        required=True,
        help="Which weight of a shipment plastic tax is charged on.",
    )
    plastic_tax_rate = fields.Monetary(
        string="Rate per kg",
        currency_field="plastic_tax_currency_id",
        default=0.30,
    )
    plastic_tax_currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.ref("base.EUR", raise_if_not_found=False),
    )

    def _get_plastic_tax(self, net_weight, gross_weight, currency, date):
        self.ensure_one()
        weight = (
            gross_weight if self.plastic_tax_basis == "gross_weight" else net_weight
        )
        weight = self.env["product.template"]._plastic_weight_to_kg(weight)
        rate_currency = self.plastic_tax_currency_id or currency
        return rate_currency._convert(
            weight * self.plastic_tax_rate, currency, self, date
        )
