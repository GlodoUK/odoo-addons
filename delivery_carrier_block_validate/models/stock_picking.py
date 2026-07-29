from odoo import models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        block_picking_ids = self.filtered(
            lambda p: p.carrier_id.block_validate and p.state != "done"
        )

        if block_picking_ids:
            block_picking_names = "\n".join(
                f"{picking.name} : {picking.carrier_id.name}"
                for picking in block_picking_ids
            )
            raise UserError(
                self.env._(
                    "Validation is blocked by the delivery method on the following transfers:\n%(pickings)s",  # noqa: E501
                    pickings=block_picking_names,
                )
            )

        return super().button_validate()
