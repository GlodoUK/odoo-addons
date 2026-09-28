import math

from odoo import api, fields, models


class StockPutInPack(models.TransientModel):
    _inherit = "stock.put.in.pack"

    auto_put_in_pack = fields.Selection(
        [("no", "Manual"), ("auto", "Auto-pack")],
        default="no",
        required=True,
        string="Mode",
    )
    missing_capacity_warning = fields.Char(
        compute="_compute_missing_capacity_warning",
    )

    @api.depends(
        "auto_put_in_pack",
        "package_type_id",
        "package_type_id.product_capacity_ids",
        "move_line_ids.product_id",
        "move_line_ids.product_uom_id",
        "move_line_ids.result_package_id",
    )
    def _compute_missing_capacity_warning(self):
        for record in self:
            if record.auto_put_in_pack != "auto" or not record.package_type_id:
                record.missing_capacity_warning = False
                continue

            capacity_keys = {
                (cap.product_id.id, cap.uom_id.id)
                for cap in record.package_type_id.product_capacity_ids
            }

            missing = []
            seen = set()
            for line in record.move_line_ids.filtered(
                lambda x: not x.result_package_id
            ):
                key = (line.product_id.id, line.product_uom_id.id)
                if key not in capacity_keys and key not in seen:
                    seen.add(key)
                    missing.append(
                        f"{line.product_id.display_name} ({line.product_uom_id.name})"
                    )

            record.missing_capacity_warning = ", ".join(missing) if missing else False

    def _action_auto_put_in_pack(self):  # noqa: C901
        self.ensure_one()
        candidates_to_split = self.move_line_ids.filtered(
            lambda x: not x.result_package_id
        )
        split_move_line_ids = self.env["stock.move.line"]
        package_max_weight = self.package_type_id.max_weight
        package_max_length = self.package_type_id.packaging_length
        package_max_width = self.package_type_id.width
        package_max_height = self.package_type_id.height
        package_volume = package_max_length * package_max_width * package_max_height

        # Pre-emptively split all stock.move.lines for anything that exceeds the
        # capacity of the package type, to make our lives easier when repackaging.
        capacity_by_product_uom = {
            (cap.product_id.id, cap.uom_id.id): cap.quantity
            for cap in self.env["stock.package.type.product.capacity"].search(
                [
                    ("product_id", "in", self.move_line_ids.mapped("product_id").ids),
                    ("package_type_id", "=", self.package_type_id.id),
                ]
            )
        }

        for candidate in candidates_to_split:
            product = candidate.product_id
            line_uom = candidate.product_uom_id

            # Determine max quantity per package in the line's UoM.
            # An exact (product, uom) match takes precedence; otherwise
            # derive from weight and volume constraints on the package type.
            capacity_key = (product.id, line_uom.id)
            if capacity_key in capacity_by_product_uom:
                max_qty_in_line_uom = capacity_by_product_uom[capacity_key]
            else:
                limits = []
                if package_max_weight and product.weight:
                    limits.append(package_max_weight / product.weight)
                if package_volume and product.volume:
                    limits.append(package_volume / product.volume)
                if not limits:
                    continue
                max_qty_in_line_uom = product.uom_id._compute_quantity(
                    max(1, math.floor(min(limits))), line_uom
                )

            if candidate.quantity <= max_qty_in_line_uom:
                continue

            # Reduce the original line to the first chunk and create new
            # lines for the remainder, each capped at max_qty_in_line_uom.
            remaining = candidate.quantity - max_qty_in_line_uom
            candidate.quantity = max_qty_in_line_uom
            while remaining > 0:
                chunk = min(remaining, max_qty_in_line_uom)
                new_line = candidate.copy(
                    {"quantity": chunk, "result_package_id": False}
                )
                split_move_line_ids |= new_line
                remaining -= chunk

        self.move_line_ids |= split_move_line_ids

        # Accumulate lines into a group until adding
        # the next line would breach any capacity, then start a new
        # group. Each group is packed in one _put_in_pack call so lines that
        # share a package are linked to the same quant_package.
        all_lines_to_pack = (candidates_to_split | split_move_line_ids).filtered(
            lambda x: not x.result_package_id
        )

        groups = []
        current_group = self.env["stock.move.line"]
        current_weight = 0.0
        current_volume = 0.0
        current_qty_by_key = {}

        for line in all_lines_to_pack:
            product = line.product_id
            qty = line.quantity
            line_weight = product.weight * qty if product.weight else 0.0
            line_volume = product.volume * qty if product.volume else 0.0
            capacity_key = (product.id, line.product_uom_id.id)

            fits = True
            if package_max_weight and product.weight:
                if current_weight + line_weight > package_max_weight:
                    fits = False
            if fits and package_volume and product.volume:
                if current_volume + line_volume > package_volume:
                    fits = False
            if fits and capacity_key in capacity_by_product_uom:
                if (
                    current_qty_by_key.get(capacity_key, 0.0) + qty
                    > capacity_by_product_uom[capacity_key]
                ):
                    fits = False

            if not fits and current_group:
                groups.append(current_group)
                current_group = self.env["stock.move.line"]
                current_weight = 0.0
                current_volume = 0.0
                current_qty_by_key = {}

            current_group |= line
            current_weight += line_weight
            current_volume += line_volume
            current_qty_by_key[capacity_key] = (
                current_qty_by_key.get(capacity_key, 0.0) + qty
            )

        if current_group:
            groups.append(current_group)

        for group in groups:
            # Calling super().action_put_in_pack() is intentionally avoided: it
            # would see all unpackaged lines and nest them into a single package,
            # or set parent_package_id on already-created packages.
            for line in group:
                # XXX: doing it with `group._put_in_pack` results in wonky results
                line._put_in_pack(package_type_id=self.package_type_id.id)

    def action_put_in_pack(self):
        if self.auto_put_in_pack == "auto":
            for record in self:
                record._action_auto_put_in_pack()
            # We also cannot fall through to super() after this loop: super()
            # would see the newly created packages as packages_to_pack and nest
            # them inside yet another package, setting parent_package_id.
            return

        return super().action_put_in_pack()
