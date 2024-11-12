from odoo import _, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_open_form(self):
        self.ensure_one()
        view = self.env.ref("stock.view_move_form")

        return {
            "name": _("Open: Stock Move"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "stock.move",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "flags": {"mode": "readonly"},
        }
