from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    active = fields.Boolean(default=True, index=True)

    def action_archive(self):
        unsafe = self.filtered(lambda x: x.state not in ("done", "cancel", "draft"))
        if unsafe:
            raise UserError(
                self.env._(
                    "There are %(count)d pickings not in a safe state to archive",
                    count=len(unsafe),
                )
            )

        return super().action_archive()
