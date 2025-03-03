from odoo import api, fields, models
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    prereserved_qty = fields.Float(
        compute="_compute_prereserved_quantities",
        store=True,
        help="Quantity going to downstream prereservation",
    )

    prereserved_available_qty = fields.Float(
        compute="_compute_prereserved_quantities",
        store=True,
        help="Demand - Prereserved",
    )

    @api.depends("prereserved_dest_ids", "product_uom_qty", "state")
    def _compute_prereserved_quantities(self):
        for record in self:
            if record.state in ("done", "cancel", "draft"):
                record.prereserved_qty = 0
                record.prereserved_available_qty = 0
                continue

            record.prereserved_qty = sum(
                record.prereserved_dest_ids.mapped("product_uom_qty_reserved")
            )
            record.prereserved_available_qty = (
                record.product_uom_qty - record.prereserved_qty
            )

    prereserved_dest_ids = fields.One2many(
        "stock.move.prereserved", "move_orig_id", readonly=True
    )

    prereserved_orig_ids = fields.One2many(
        "stock.move.prereserved", "move_dest_id", readonly=True
    )

    def action_unlink_move_orig_ids(self):
        moves = self.filtered(
            lambda m: m.state not in self._get_unlink_move_orig_ids_states()
        )

        return self.env["stock.move.prereserved"]._unlink_orig_moves(
            moves, remove_all=True
        )

    show_action_link_move_orig_ids = fields.Boolean(
        compute="_compute_show_move_orig_ids_actions", store=False
    )

    show_action_unlink_move_orig_ids = fields.Boolean(
        compute="_compute_show_move_orig_ids_actions", store=False
    )

    move_dest_id_count = fields.Integer(
        compute="_compute_move_dest_orig_count", store=True
    )

    move_orig_id_count = fields.Integer(
        compute="_compute_move_dest_orig_count",
        store=True,
    )

    @api.depends("move_dest_ids", "move_orig_ids")
    def _compute_move_dest_orig_count(self):
        for record in self:
            record.move_dest_id_count = len(record.move_dest_ids)
            record.move_orig_id_count = len(record.move_orig_ids)

    @api.depends("move_orig_ids")
    def _compute_show_move_orig_ids_actions(self):
        for record in self:
            record.show_action_link_move_orig_ids = (
                record.state in self._get_link_move_orig_ids_states()
            )
            record.show_action_unlink_move_orig_ids = (
                record.state not in self._get_unlink_move_orig_ids_states()
                and record.move_orig_ids
            )

    @api.depends("move_dest_ids")
    def _compute_show_move_dest_ids_actions(self):
        for record in self:
            record.show_action_unlink_move_dest_ids = record.move_dest_ids

    def _get_candidate_future_moves_domain(self):
        self.ensure_one()
        return [
            ("location_dest_id", "=", self.location_id.id),
            ("state", "not in", self._get_unlink_move_orig_ids_states()),
            ("product_id", "=", self.product_id.id),
            # only support the same UoM for now. This is to avoid
            # potentially slow conversion issues
            ("product_uom", "=", self.product_uom.id),
            # don't recursively link in the weird scenario where someone's
            # managed to setup a transfer to and from the same location
            ("id", "not in", self.ids),
        ]

    @api.model
    def _get_link_move_orig_ids_states(self):
        return [
            "assigned",
            "confirmed",
            "partially_available",
        ]

    @api.model
    def _get_unlink_move_orig_ids_states(self):
        return ["draft", "cancel", "done"]

    @api.model
    def _get_candidate_future_moves_order(self):
        return "date asc"

    def _get_candidate_future_moves(self):
        self.ensure_one()
        move_id = self

        candidates = self.env["stock.move"].search(
            self._get_candidate_future_moves_domain(),
            order=self._get_candidate_future_moves_order(),
        )

        candidates = candidates.filtered(
            lambda c: float_compare(
                sum(c.move_dest_ids.mapped("product_uom_qty")),
                c.product_uom_qty,
                precision_rounding=move_id.product_uom.rounding,
            )
            <= 0
        )

        return candidates

    def _action_cancel(self):
        # before cancelling we need to break any manually created links to
        # prevent it propagating up the tree
        self.env["stock.move.prereserved"]._unlink_orig_moves(self)
        self.env["stock.move.prereserved"]._unlink_dest_moves(self)

        return super()._action_cancel()

    def write(self, vals):
        res = super().write(vals)
        if "product_uom_qty" in vals:
            self.env["stock.move.prereserved"].sudo()._recalculate_dest_reserved_qty(
                self
            )

        return res
