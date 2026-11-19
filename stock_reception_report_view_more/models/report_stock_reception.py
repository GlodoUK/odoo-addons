from collections import defaultdict

from odoo import api, models
from odoo.exceptions import UserError


class ReportStockReport_Reception(models.AbstractModel):
    _inherit = "report.stock.report_reception"

    @api.model
    def get_report_data(self, docids, data):
        # Only the on-screen report gets the extra lines, never the PDF.
        return super(
            ReportStockReport_Reception,
            self.with_context(reception_report_view_more=True),
        ).get_report_data(docids, data)

    @api.model
    def _get_report_values(self, docids, data=None):
        values = super()._get_report_values(docids, data=data)
        docs = values.get("docs")
        if not docs or not self.env.context.get("reception_report_view_more"):
            return values
        self._add_full_quantities(values)
        self._add_view_more_lines(values)
        return values

    def _add_full_quantities(self, values):
        """Flag part-fulfilled lines with the full quantity the transfer needs.

        The standard report only shows what the incoming stock can cover. The
        UI uses ``full_quantity`` when "View more" is on, while ``quantity``
        stays the assignable amount.
        """
        done = "done" in values["docs"].mapped("state")
        for lines in values["sources_to_lines"].values():
            for line in lines:
                if line["is_assigned"] or not line["is_qty_assignable"]:
                    continue
                out = line["move_out"]
                uom = out.product_id.uom_id
                full = out.product_qty
                if not done and out.state == "partially_available":
                    full -= out.product_uom._compute_quantity(out.quantity, uom)
                if uom.compare(full, line["quantity"]) > 0:
                    line["full_quantity"] = full

    def _add_view_more_lines(self, values):
        docs = values["docs"]
        sources_to_lines = values["sources_to_lines"]
        doc_states = docs.mapped("state")

        # Incoming quantity still not linked to an outgoing move, per product.
        product_to_remaining = defaultdict(float)
        product_to_ins = defaultdict(lambda: self.env["stock.move"])
        for move in self._get_moves(docs):
            if move.state == "draft":
                continue
            move_qty = move.product_qty or move.product_uom._compute_quantity(
                move.quantity, move.product_id.uom_id, rounding_method="HALF-UP"
            )
            remaining = move_qty - sum(move.move_dest_ids.mapped("product_qty"))
            if move.product_id.uom_id.compare(remaining, 0) > 0:
                product_to_remaining[move.product_id] += remaining
                product_to_ins[move.product_id] |= move
        if not product_to_remaining:
            return

        # Same candidates as the standard report.
        warehouse = docs[0].picking_type_id.warehouse_id
        wh_location_ids = self.env["stock.location"]._search(
            [
                ("id", "child_of", warehouse.view_location_id.id),
                ("usage", "!=", "supplier"),
            ]
        )
        allowed_states = ["confirmed", "partially_available", "waiting"]
        if "done" in doc_states:
            allowed_states += ["assigned"]
        outs = self.env["stock.move"].search(
            [
                ("state", "in", allowed_states),
                ("product_qty", ">", 0),
                ("location_id", "in", wh_location_ids),
                ("move_orig_ids", "=", False),
                ("product_id", "in", [p.id for p in product_to_remaining]),
            ]
            + self._get_extra_domain(docs),
            order="reservation_date, priority desc, date, id",
        )

        shown = {
            line["move_out"].id for lines in sources_to_lines.values() for line in lines
        }
        for out in outs:
            if out.id in shown:
                continue
            source = self._get_report_source(out)
            if not source:
                continue
            product = out.product_id
            uom = product.uom_id
            qty_to_reserve = out.product_qty
            if "done" not in doc_states and out.state == "partially_available":
                qty_to_reserve -= out.product_uom._compute_quantity(out.quantity, uom)
            quantity = min(qty_to_reserve, product_to_remaining[product])
            if uom.is_zero(quantity):
                continue
            line = self._prepare_report_line(
                quantity,
                product,
                out,
                source[0],
                move_ins=product_to_ins[product],
            )
            line["is_extra"] = True
            if uom.compare(qty_to_reserve, quantity) > 0:
                line["full_quantity"] = qty_to_reserve
            sources_to_lines[source].append(line)

        sources_to_dates = values["sources_to_formatted_scheduled_date"]
        for source in sources_to_lines:
            if source not in sources_to_dates:
                sources_to_dates[source] = self._get_formatted_scheduled_date(source[0])

    def action_assign(self, move_ids, qtys, in_ids):
        self._check_incoming_not_over_assigned(move_ids, qtys, in_ids)
        return super().action_assign(move_ids, qtys, in_ids)

    def _check_incoming_not_over_assigned(self, move_ids, qtys, in_ids):
        """Refuse to link more than the incoming moves have left unlinked.

        The report only offers each unit of incoming stock once, but extra
        lines can be assigned in any order, so check at assign time.
        """
        Move = self.env["stock.move"]
        needed = defaultdict(float)
        incoming = defaultdict(lambda: Move)
        for move_id, qty, ins in zip(move_ids, qtys, in_ids, strict=False):
            out = Move.browse(move_id)
            in_moves = Move.browse(ins)
            if not in_moves or out in in_moves.move_dest_ids:
                # Nothing to link, or already linked (e.g. a repeated click).
                continue
            needed[out.product_id] += qty
            incoming[out.product_id] |= in_moves
        for product, qty_needed in needed.items():
            uom = product.uom_id
            available = 0.0
            for in_move in incoming[product]:
                in_qty = in_move.product_qty or in_move.product_uom._compute_quantity(
                    in_move.quantity, uom, rounding_method="HALF-UP"
                )
                available += max(
                    in_qty - sum(in_move.move_dest_ids.mapped("product_qty")), 0.0
                )
            if uom.compare(qty_needed, available) > 0:
                raise UserError(
                    self.env._(
                        "Only %(available)s %(uom)s of %(product)s is still "
                        "unallocated on the incoming transfer, but %(needed)s "
                        "was requested. Unassign another transfer first.",
                        available=available,
                        uom=uom.display_name,
                        product=product.display_name,
                        needed=qty_needed,
                    )
                )
