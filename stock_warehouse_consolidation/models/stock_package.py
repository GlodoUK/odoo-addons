from odoo import Command, api, fields, models
from odoo.tools import float_compare


class StockPackage(models.Model):
    _inherit = "stock.package"

    can_be_consolidated = fields.Boolean(
        related="package_type_id.can_be_consolidated",
        store=True,
        index=True,
    )

    package_product_id = fields.Many2one(
        "product.product",
        string="Product",
        compute="_compute_package_content",
        store=True,
        help="The single product stored on this package.",
    )

    content_qty = fields.Float(
        string="On Hand",
        compute="_compute_package_content",
        store=True,
        digits="Product Unit of Measure",
    )

    reserved_qty = fields.Float(
        string="Reserved",
        compute="_compute_package_content",
        store=True,
        digits="Product Unit of Measure",
    )

    capacity_qty = fields.Float(
        string="Capacity",
        compute="_compute_capacity",
        digits="Product Unit of Measure",
    )

    remaining_qty = fields.Float(
        string="Remaining",
        compute="_compute_capacity",
        digits="Product Unit of Measure",
    )

    fill_pct = fields.Float(
        string="Fill %",
        compute="_compute_capacity",
    )

    @api.depends(
        "can_be_consolidated",
        "quant_ids.quantity",
        "quant_ids.reserved_quantity",
        "quant_ids.product_id",
    )
    def _compute_package_content(self):
        for package in self:
            if not package.can_be_consolidated:
                # Only consolidatable packages carry these figures.
                package.package_product_id = False
                package.content_qty = 0.0
                package.reserved_qty = 0.0
                continue

            products = package.quant_ids.product_id
            package.package_product_id = products if len(products) == 1 else False
            package.content_qty = sum(package.quant_ids.mapped("quantity"))
            package.reserved_qty = sum(package.quant_ids.mapped("reserved_quantity"))

    @api.depends("package_product_id", "package_type_id", "content_qty")
    def _compute_capacity(self):
        packages = self.filtered(
            lambda p: (
                p.can_be_consolidated and p.package_product_id and p.package_type_id
            )
        )

        cap_map = {}

        if packages:
            capacities = self.env["consolidation.package.capacity"].search(
                [
                    ("product_id", "in", packages.package_product_id.ids),
                    ("package_type_id", "in", packages.package_type_id.ids),
                ]
            )
            cap_map = {
                (c.product_id.id, c.package_type_id.id): c.max_qty for c in capacities
            }

        for package in self:
            capacity = cap_map.get(
                (package.package_product_id.id, package.package_type_id.id), 0.0
            )
            package.capacity_qty = capacity
            package.remaining_qty = capacity - package.content_qty
            package.fill_pct = (
                (package.content_qty / capacity * 100.0) if capacity else 0.0
            )

    def action_open_consolidation_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Consolidate Packages"),
            "res_model": "consolidation.package.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_package_ids": [Command.set(self.ids)]},
        }

    def action_open_relocation_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Relocate Packages"),
            "res_model": "consolidation.location.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_package_ids": [Command.set(self.ids)]},
        }

    @api.model
    def _find_consolidation_candidates(self):
        warehouses = self.env["stock.warehouse"].search_fetch([], ["lot_stock_id"])

        packages = self.search(
            [
                ("can_be_consolidated", "=", True),
                ("content_qty", ">", 0),
                ("package_product_id", "!=", False),
                ("package_type_id", "!=", False),
                ("location_id", "child_of", warehouses.lot_stock_id.ids),
            ]
        )

        # A full package has no room to absorb another one.
        packages = packages.filtered(
            lambda p: (
                float_compare(
                    p.remaining_qty,
                    0.0,
                    precision_rounding=p.package_product_id.uom_id.rounding,
                )
            )
            > 0
        )

        groups = {}

        for package in packages:
            key = (
                package.package_product_id.id,
                package.package_type_id.id,
                package.location_id.warehouse_id.id,
            )

            groups.setdefault(key, self.browse())
            groups[key] |= package

        cap_map = {}

        if packages:
            capacities = self.env["consolidation.package.capacity"].search(
                [
                    ("product_id", "in", packages.package_product_id.ids),
                    ("package_type_id", "in", packages.package_type_id.ids),
                ]
            )

            cap_map = {
                (c.product_id.id, c.package_type_id.id): c.max_qty for c in capacities
            }

        candidates = self.browse()

        for (product_id, package_type_id, _warehouse_id), group in groups.items():
            capacity = cap_map.get((product_id, package_type_id), 0.0)

            if len(group) < 2 or capacity <= 0:
                continue

            rounding = group[0].package_product_id.uom_id.rounding
            # A package qualifies if it fits with the smallest other in its group.
            quantities = sorted(group.mapped("content_qty"))

            for package in group:
                smallest_other = (
                    quantities[1]
                    if package.content_qty == quantities[0]
                    else quantities[0]
                )

                combined = package.content_qty + smallest_other

                if float_compare(combined, capacity, precision_rounding=rounding) <= 0:
                    candidates |= package

        return candidates
