from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class WizardSaleOrderUnhold(models.TransientModel):
    _name = "wizard.sale.order.unhold"
    _description = "Sale Order Unhold Wizard"

    sale_ids = fields.Many2many(
        "sale.order",
        required=True,
    )

    msg = fields.Text(
        string="Optional Message",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        if self.env.context.get("active_model") != "sale.order":
            msg = _("This can only be used on sale orders.")
            raise UserError(msg)

        if "sale_ids" in fields:
            res["sale_ids"] = [Command.set(self.env.context.get("active_ids"))]

        return res

    def process(self):
        self.ensure_one()

        self.sale_ids.action_unhold(msg=self.msg)
