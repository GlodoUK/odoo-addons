from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class ConsolidationPackageWizard(models.TransientModel):
    _name = "consolidation.package.wizard"
    _description = "Consolidate Packages"

    package_ids = fields.Many2many(
        "stock.package",
        string="Packages",
        required=True,
    )

    product_id = fields.Many2one(
        "product.product",
        compute="_compute_product_id",
    )

    target_package_id = fields.Many2one(
        "stock.package",
        required=True,
        domain="[('id', 'in', package_ids)]",
        help="The package the others will be merged into.",
    )

    dest_location_id = fields.Many2one(
        "stock.location",
        related="target_package_id.location_id",
        string="Destination Location",
        help="Stock is moved into the target package's location.",
    )

    @api.depends("package_ids")
    def _compute_product_id(self):
        for wizard in self:
            wizard.product_id = wizard.package_ids.mapped("package_product_id")[:1]

    @api.onchange("package_ids")
    def _onchange_package_ids(self):
        if self.package_ids and self.target_package_id not in self.package_ids:
            # Default to the fullest package to move as little as possible.
            self.target_package_id = max(self.package_ids, key=lambda p: p.content_qty)

    def action_consolidate(self):
        self.ensure_one()

        packages = self.package_ids

        if len(packages) < 2:
            raise UserError(self.env._("Select at least two packages to consolidate."))

        product = packages.package_product_id

        if len(product) != 1:
            raise UserError(
                self.env._("All packages must contain the same single product.")
            )
        if len(packages.package_type_id) != 1:
            raise UserError(
                self.env._("All packages must be of the same package type.")
            )
        if len(packages.location_id.warehouse_id) != 1:
            raise UserError(
                self.env._("All packages must belong to the same warehouse.")
            )

        target = self.target_package_id
        if target not in packages:
            raise UserError(
                self.env._("The target package must be one of the selected packages.")
            )

        rounding = product.uom_id.rounding
        sources = packages - target

        reserved = sources.filtered(
            lambda p: not float_is_zero(p.reserved_qty, precision_rounding=rounding)
        )
        if reserved:
            raise UserError(
                self.env._(
                    "These packages hold reserved stock and cannot be consolidated"
                    " until it is released or deselected: %(packages)s",
                    packages=", ".join(reserved.mapped("name")),
                )
            )

        capacity = self.env["consolidation.package.capacity"]._get_capacity(
            product, target.package_type_id
        )

        if capacity <= 0:
            raise UserError(
                self.env._(
                    "No package capacity is defined for %(product)s. Add one in"
                    " the Package Capacities configuration first.",
                    product=product.display_name,
                )
            )

        quants = sources.quant_ids.filtered(
            lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0
        )

        if not quants:
            raise UserError(self.env._("There is no stock to consolidate."))

        total_to_move = sum(quants.mapped("quantity"))

        if (
            float_compare(
                target.content_qty + total_to_move,
                capacity,
                precision_rounding=rounding,
            )
            > 0
        ):
            raise UserError(
                self.env._(
                    "The combined stock exceeds the capacity of the target"
                    " package (%(capacity)s).",
                    capacity=capacity,
                )
            )

        picking = self._create_consolidation_picking(product, target, quants)

        return {
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "res_id": picking.id,
            "view_mode": "form",
            "target": "current",
        }

    def _create_consolidation_picking(self, product, target, quants):
        dest = target.location_id
        picking_type = dest._get_consolidation_picking_type()

        by_location = quants.grouped("location_id")
        source_locations = list(by_location)

        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": source_locations[0].id,
                "location_dest_id": dest.id,
                "origin": self.env._("Package consolidation: %s", product.display_name),
            }
        )

        moves = []
        for source_location, move_quants in by_location.items():
            move = self.env["stock.move"].create(
                {
                    "product_id": product.id,
                    "product_uom": product.uom_id.id,
                    "product_uom_qty": sum(move_quants.mapped("quantity")),
                    "location_id": source_location.id,
                    "location_dest_id": dest.id,
                    "picking_id": picking.id,
                }
            )
            moves.append((move, move_quants))

        picking.action_confirm()
        # Replace lines auto-reserved on confirm so we reserve exactly once.
        picking.move_line_ids.unlink()

        for move, move_quants in moves:
            for quant in move_quants:
                self.env["stock.move.line"].create(
                    {
                        "move_id": move.id,
                        "picking_id": picking.id,
                        "product_id": product.id,
                        "product_uom_id": product.uom_id.id,
                        "quantity": quant.quantity,
                        "location_id": quant.location_id.id,
                        "location_dest_id": dest.id,
                        "package_id": quant.package_id.id,
                        "result_package_id": target.id,
                        "lot_id": quant.lot_id.id,
                    }
                )

        return picking
