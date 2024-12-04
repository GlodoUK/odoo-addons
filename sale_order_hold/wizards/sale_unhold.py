from odoo import api, fields, models


class SaleUnhold(models.TransientModel):
    _name = "wizard.sale.order.unhold"
    _description = "Sale Order Unhold Wizard"

    sale_ids = fields.Many2many("sale.order", required=True)
    msg = fields.Text(string="Extended Message")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        sale_ids = self.env.context["active_ids"] or []
        active_model = self.env.context["active_model"]

        if not sale_ids:
            return res
        assert active_model == "sale.order", "Bad context propagation"

        res["sale_ids"] = [(6, False, sale_ids)]
        return res

    def process(self):
        self.ensure_one()
        self.sale_ids.action_unhold(msg=self.msg)
