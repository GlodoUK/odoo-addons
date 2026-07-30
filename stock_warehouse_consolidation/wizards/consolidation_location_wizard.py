from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class ConsolidationLocationWizard(models.TransientModel):
    _name = "consolidation.location.wizard"
    _description = "Relocate Packages"

    package_ids = fields.Many2many(
        "stock.package",
        string="Packages",
        required=True,
    )

    dest_location_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        required=True,
        domain="[('id', 'in', allowed_dest_location_ids)]",
        help="Every selected package is moved into this location.",
    )

    allowed_dest_location_ids = fields.Many2many(
        "stock.location",
        compute="_compute_allowed_dest_location_ids",
        help=(
            "Same-warehouse locations with enough free package slots to absorb"
            " the selected packages."
        ),
    )

    @api.depends("package_ids")
    def _compute_allowed_dest_location_ids(self):
        for wizard in self:
            packages = wizard.package_ids
            warehouses = packages.location_id.warehouse_id

            if not packages or not warehouses:
                wizard.allowed_dest_location_ids = False
                continue

            candidates = self.env["stock.location"].search(
                [
                    ("usage", "=", "internal"),
                    ("warehouse_id", "in", warehouses.ids),
                    (
                        "storage_category_id.capacity_ids.package_type_id.can_be_consolidated",
                        "=",
                        True,
                    ),
                ]
            )

            wizard.allowed_dest_location_ids = candidates.filtered(
                lambda location, packages=packages: (
                    location.free_package_slots
                    >= len(packages.filtered(lambda p: p.location_id != location))
                )
            )

    @api.onchange("package_ids")
    def _onchange_package_ids(self):
        allowed = self.allowed_dest_location_ids
        if self.package_ids and self.dest_location_id not in allowed:
            # Tightest fit: filling the fullest location frees the most others.
            self.dest_location_id = (
                min(allowed, key=lambda loc: loc.free_package_slots)
                if allowed
                else False
            )

    def action_relocate(self):
        self.ensure_one()

        packages = self.package_ids
        dest = self.dest_location_id

        if not packages:
            raise UserError(self.env._("Select at least one package to relocate."))
        if packages.filtered(lambda p: not p.can_be_consolidated):
            raise UserError(
                self.env._("Only consolidatable packages can be relocated.")
            )
        if len(packages.location_id.warehouse_id) != 1:
            raise UserError(
                self.env._("All packages must belong to the same warehouse.")
            )

        if dest.warehouse_id != packages.location_id.warehouse_id:
            raise UserError(
                self.env._(
                    "The destination must be in the same warehouse as the packages."
                )
            )

        moving = packages.filtered(lambda p: p.location_id != dest)
        if not moving:
            raise UserError(
                self.env._("Every selected package is already in that location.")
            )

        reserved = moving.filtered(
            lambda p: (
                not float_is_zero(
                    p.reserved_qty,
                    precision_rounding=p.package_product_id.uom_id.rounding or 0.01,
                )
            )
        )

        if reserved:
            raise UserError(
                self.env._(
                    "These packages hold reserved stock and cannot be relocated"
                    " until it is released or deselected: %(packages)s",
                    packages=", ".join(reserved.mapped("name")),
                )
            )

        self._check_destination_capacity(moving, dest)
        picking = self._create_relocation_picking(moving, dest)

        return {
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "res_id": picking.id,
            "view_mode": "form",
            "target": "current",
        }

    def _check_destination_capacity(self, packages, dest):
        count_by_type = {}

        for package in packages:
            package_type = package.package_type_id
            if package_type not in count_by_type:
                count_by_type[package_type] = self.env["stock.package"].search_count(
                    [
                        ("location_id", "=", dest.id),
                        ("package_type_id", "=", package_type.id),
                    ]
                )

            if not dest._check_can_be_used(
                package.package_product_id,
                package=package,
                location_qty=count_by_type[package_type],
            ):
                raise UserError(
                    self.env._(
                        "%(location)s cannot absorb %(package)s: it is out of"
                        " space for this package type, or its storage category"
                        " does not allow it.",
                        location=dest.display_name,
                        package=package.name,
                    )
                )

            count_by_type[package_type] += 1

    def _create_relocation_picking(self, packages, dest):
        picking_type = dest._get_consolidation_picking_type()

        quants = packages.quant_ids

        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": quants[:1].location_id.id,
                "location_dest_id": dest.id,
                "origin": self.env._("Package relocation to %s", dest.display_name),
            }
        )

        moves = []
        for (product, source_location), move_quants in quants.grouped(
            lambda q: (q.product_id, q.location_id)
        ).items():
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
                        "product_id": quant.product_id.id,
                        "product_uom_id": quant.product_id.uom_id.id,
                        "quantity": quant.quantity,
                        "location_id": quant.location_id.id,
                        "location_dest_id": dest.id,
                        "package_id": quant.package_id.id,
                        "result_package_id": quant.package_id.id,
                        "lot_id": quant.lot_id.id,
                    }
                )
        return picking
