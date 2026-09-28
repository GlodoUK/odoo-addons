from odoo import api, fields, models
from odoo.exceptions import UserError


class StockLocation(models.Model):
    _inherit = "stock.location"

    package_capacity = fields.Integer(
        compute="_compute_package_slots",
        help=(
            "How many packages this location holds, from its storage category's"
            " package capacity lines for package types."
        ),
    )

    package_count = fields.Integer(
        string="Packages Stored",
        compute="_compute_package_slots",
    )

    free_package_slots = fields.Integer(
        compute="_compute_package_slots",
    )

    def _compute_package_slots(self):
        counts = {
            location.id: count
            for location, count in self.env["stock.package"]._read_group(
                [("location_id", "in", self.ids), ("can_be_consolidated", "=", True)],
                groupby=["location_id"],
                aggregates=["__count"],
            )
        }

        for location in self:
            capacity = int(
                sum(
                    location.storage_category_id.package_capacity_ids.filtered(
                        lambda c: c.package_type_id.can_be_consolidated
                    ).mapped("quantity")
                )
            )
            count = counts.get(location.id, 0)
            location.package_capacity = capacity
            location.package_count = count
            location.free_package_slots = max(capacity - count, 0)

    @api.model
    def _find_underfilled_package_locations(self):
        locations = self.search(
            [
                ("usage", "=", "internal"),
                (
                    "storage_category_id.capacity_ids.package_type_id.can_be_consolidated",
                    "=",
                    True,
                ),
            ]
        )

        return locations.filtered(
            lambda location: 0 < location.package_count < location.package_capacity
        )

    def _get_consolidation_picking_type(self):
        self.ensure_one()

        picking_type = self.warehouse_id.int_type_id
        if not picking_type:
            raise UserError(
                self.env._(
                    "%(warehouse)s has no internal transfer operation type.",
                    warehouse=self.warehouse_id.display_name or self.display_name,
                )
            )

        return picking_type
