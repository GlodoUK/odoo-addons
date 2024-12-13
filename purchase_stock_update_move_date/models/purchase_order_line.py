from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def write(self, vals):
        if vals.get("date_planned"):
            new_date = fields.Datetime.to_datetime(vals["date_planned"])

            self.filtered(lambda line: not line.display_type)._update_move_date(
                new_date
            )

        return super().write(vals)

    def _update_move_date(self, new_date):
        moves_to_update = self.move_ids.filtered(
            lambda m: m.state not in ("done", "cancel")
        )
        moves_to_update.date = new_date
