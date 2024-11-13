from odoo import _, api, exceptions, fields, models


class StockMoveFutureCandidate(models.TransientModel):
    _name = "stock.move.future.candidate"
    _description = "Stock Move Future Candidate"

    wizard_id = fields.Many2one("stock.move.future", required=True)

    src_move_id = fields.Many2one("stock.move", string="Inbound Move", required=True)
    src_move_uom = fields.Many2one(related="src_move_id.product_uom", store=True)
    max_qty = fields.Float(string="Available Qty")

    date = fields.Datetime(related="src_move_id.date")
    picking_id = fields.Many2one(related="src_move_id.picking_id", store=False)

    selected = fields.Boolean(default=False)


class StockMoveFuture(models.TransientModel):
    _name = "stock.move.future"
    _description = "Stock Move Future"

    move_id = fields.Many2one("stock.move", required=True)
    move_required = fields.Float(
        compute="_compute_move_required",
        store=False,
        string="Outstanding",
    )

    @api.depends("move_id")
    def _compute_move_required(self):
        for record in self:
            if not record.move_id:
                record.move_required = 0.0
                continue
            record.move_required = (
                record.move_id.product_uom_qty - record.move_id.reserved_availability
            )

    move_uom = fields.Many2one(related="move_id.product_uom", store=False)

    candidate_move_ids = fields.One2many("stock.move.future.candidate", "wizard_id")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        move_id = self.env.context.get("default_move_id", [])

        move_id = self.env["stock.move"].browse(move_id)

        candidates = move_id._get_candidate_future_moves()
        res["candidate_move_ids"] = [
            (
                0,
                0,
                {
                    "src_move_id": candidate.id,
                    "src_move_uom": candidate.product_uom.id,
                    "max_qty": candidate.product_uom_qty
                    - sum(
                        candidate.move_dest_ids.mapped(
                            lambda c: c.product_uom_qty - c.reserved_availability
                        )
                    ),
                    "date": candidate.date,
                    "picking_id": candidate.picking_id.id,
                },
            )
            for candidate in candidates
        ]
        return res

    def action_link(self):
        candidates = self.candidate_move_ids.filtered(lambda c: c.selected)
        if not candidates:
            raise exceptions.UserError(_("No candidates selected."))

        for candidate in candidates:
            self.env["stock.move.prereserved"]._link_moves(
                candidate.src_move_id, self.move_id, unreserve=True
            )
