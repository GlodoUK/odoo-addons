from odoo import api, fields, models
from odoo.exceptions import UserError


class ConsolidationPackageLine(models.TransientModel):
    _name = "consolidation.package.line"
    _description = "Package to Consolidate"
    _order = "product_id, id"

    package_id = fields.Many2one(
        "stock.package",
        string="Package",
        required=True,
        readonly=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        readonly=True,
    )

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse",
        readonly=True,
    )

    location_id = fields.Many2one(
        "stock.location",
        string="Location",
        readonly=True,
    )

    content_qty = fields.Float(
        string="On Hand",
        digits="Product Unit of Measure",
        readonly=True,
    )

    capacity_qty = fields.Float(
        string="Capacity",
        digits="Product Unit of Measure",
        readonly=True,
    )

    fill_pct = fields.Float(
        string="Fill %",
        readonly=True,
    )

    @api.model
    def action_open(self):
        candidates = self.env["stock.package"]._find_consolidation_candidates()

        lines = self.create(
            [
                {
                    "package_id": package.id,
                    "product_id": package.package_product_id.id,
                    "warehouse_id": package.location_id.warehouse_id.id,
                    "location_id": package.location_id.id,
                    "content_qty": package.content_qty,
                    "capacity_qty": package.capacity_qty,
                    "fill_pct": package.fill_pct,
                }
                for package in candidates
            ]
        )

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Packages to Consolidate"),
            "res_model": self._name,
            "view_mode": "list",
            "views": [
                (
                    self.env.ref(
                        "stock_warehouse_consolidation"
                        ".consolidation_package_line_view_list"
                    ).id,
                    "list",
                )
            ],
            "domain": [("id", "in", lines.ids)],
            "context": {"group_by": ["product_id"]},
            "target": "current",
            "help": self.env._(
                "<p class='o_view_nocontent_smiling_face'>Nothing to"
                " consolidate</p><p>No two packages of the same product, package"
                " type and warehouse currently fit on a single package.</p>"
            ),
        }

    def action_consolidate(self):
        packages = self.package_id
        if len(packages) < 2:
            raise UserError(self.env._("Select at least two packages to consolidate."))
        return packages.action_open_consolidation_wizard()
