from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"
    note = fields.Text(string="Inventory Adjustment Reason")

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        res = super()._get_inventory_move_values(
            qty, location_id, location_dest_id, out=out
        )

        res.update(
            {
                "note": self.note,
            }
        )

        return res

    def _apply_inventory(self):
        res = super()._apply_inventory()

        self.write({"note": False})

        return res

    @api.model
    def _get_inventory_fields_write(self):
        res = super()._get_inventory_fields_write()
        res.append("note")
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    note = fields.Text()


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    note = fields.Text(
        related="move_id.note",
    )
