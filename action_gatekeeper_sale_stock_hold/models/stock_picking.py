from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    gatekeeper_hold = fields.Boolean(
        default=False,
        help="Indicates whether this picking is on hold due by Gatekeeper.",
    )

    def action_unhold(self, **kwargs):
        for picking in self:
            if picking.gatekeeper_hold:
                raise UserError(
                    self.env._(
                        "Cannot unhold picking on Gatekeeper Hold: %s"
                        "\nUnhold the Sale Order first.",
                        picking.name,
                    )
                )
        res = super().action_unhold(**kwargs)
        return res

    def action_cancel(self):
        self.filtered("gatekeeper_hold").write({"gatekeeper_hold": False})
        return super().action_cancel()
