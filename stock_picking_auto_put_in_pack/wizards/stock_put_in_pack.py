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

    def _action_auto_put_in_pack(self):
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

        # Build a lookup keyed by (product_id, uom_id) so that capacities
        # for different UoMs are kept distinct and matched exactly — no
        # automatic conversion.  A "pack of 4" may physically differ from
        # 4x "each", so the caller must define the capacity in the UoM
        # they actually use on the move line.
        capacity_by_product_uom = {
            (cap.product_id.id, cap.uom_id.id): cap.quantity
            for cap in self.package_type_id.product_capacity_ids
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

        # Each chunk must go into its own package.
        # Calling super().action_put_in_pack() would pack all unpackaged lines into one,
        # so we assign packages individually here.
        for line in (candidates_to_split | split_move_line_ids).filtered(
            lambda x: not x.result_package_id
        ):
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
