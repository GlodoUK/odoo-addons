from odoo import api, fields, models


class Salehold(models.TransientModel):
    _name = "wizard.sale.order.hold"
    _description = "Sale Order Hold Wizard"

    sale_ids = fields.Many2many("sale.order", required=True)
    reason_ids = fields.Many2many(
        "sale.order.hold.reason",
        required=True,
        ondelete="cascade",
    )
    msg = fields.Text(string="Optional Extended Message")

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
        self.sale_ids.action_hold(self.reason_ids, msg=self.msg)
