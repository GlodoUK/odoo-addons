from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    show_stock_barcode_putaway_rules = fields.Boolean(
        related="picking_type_id.show_stock_barcode_putaway_rules"
    )

    def apply_putaway_strategy(self):
        self.ensure_one()
        if self.show_stock_barcode_putaway_rules:
            self.move_line_ids._apply_putaway_strategy()

    def _get_fields_stock_barcode(self):
        res = super()._get_fields_stock_barcode()
        res.extend(["show_stock_barcode_putaway_rules"])
        return res
