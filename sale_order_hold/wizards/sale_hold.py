from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class WizardSaleOrderHold(models.TransientModel):
    _name = "wizard.sale.order.hold"
    _description = "Sale Order Hold Wizard"

    reason_ids = fields.Many2many(
        "sale.order.hold.reason",
        ondelete="cascade",
        required=True,
    )

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

        self.sale_ids.action_hold(
            reason_id=self.reason_ids,
            msg=self.msg,
        )
