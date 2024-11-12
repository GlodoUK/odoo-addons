from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    move_ids_with_orig = fields.One2many(
        "stock.move.prereserved",
        compute="_compute_move_ids_with_orig",
        string="Origin Moves",
        help="Origin moves",
        readonly=True,
    )

    move_ids_with_orig_count = fields.Integer(compute="_compute_move_ids_with_orig")

    move_ids_with_dest = fields.One2many(
        "stock.move.prereserved",
        compute="_compute_move_ids_with_dest",
        string="Destinations Moves",
        help="Destination moves",
        readonly=True,
    )

    move_ids_with_dest_count = fields.Integer(compute="_compute_move_ids_with_dest")

    def _compute_move_ids_with_dest(self):
        for record in self:

            record.move_ids_with_dest = self.env["stock.move.prereserved"].search(
                [("orig_picking_id", "=", record.id)]
            )

            record.move_ids_with_dest_count = len(record.move_ids_with_dest)

    def _compute_move_ids_with_orig(self):
        for record in self:
            record.move_ids_with_orig = self.env["stock.move.prereserved"].search(
                [("dest_picking_id", "=", record.id)]
            )
            record.move_ids_with_orig_count = len(record.move_ids_with_orig)
