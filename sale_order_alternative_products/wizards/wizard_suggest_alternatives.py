from odoo import fields, models


class WizardSuggestAlternatives(models.TransientModel):
    _name = "wizard.suggest_alternatives"
    _description = "Suggest Alternatives"

    order_line_id = fields.Many2one(
        "sale.order.line", string="Order Line", readonly=True
    )
    demand = fields.Float()
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    alternative_ids = fields.Many2many(
        "product.product", string="Alternatives", readonly=True
    )
    use_alt = fields.Many2one("product.product", string="Use Alternative")

    def action_replace(self):
        self.order_line_id.product_id = self.use_alt.id
        self.order_line_id.product_id_change()
