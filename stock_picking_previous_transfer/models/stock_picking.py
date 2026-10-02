from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    show_previous_pickings = fields.Boolean(compute="_compute_show_previous_pickings")

    def _get_previous_transfers(self):
        # A return's "Return of" isn't a step before it
        previous = self.move_ids.move_orig_ids.picking_id
        return previous.filtered(lambda picking: picking not in self.return_id)

    @api.depends("move_ids.move_orig_ids")
    def _compute_show_previous_pickings(self):
        for picking in self:
            picking.show_previous_pickings = bool(picking._get_previous_transfers())

    def action_previous_transfer(self):
        previous = self._get_previous_transfers()
        if len(previous) == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "views": [[False, "form"]],
                "res_id": previous.id,
            }
        return {
            "name": self.env._("Previous Transfers"),
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "views": [[False, "list"], [False, "form"]],
            "domain": [("id", "in", previous.ids)],
        }
