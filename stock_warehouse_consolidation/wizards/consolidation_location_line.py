from odoo import api, fields, models
from odoo.exceptions import UserError


class ConsolidationLocationLine(models.TransientModel):
    _name = "consolidation.location.line"
    _description = "Package to Relocate"
    _order = "product_id, package_location_id, id"

    package_id = fields.Many2one(
        "stock.package",
        required=True,
        readonly=True,
    )

    package_location_id = fields.Many2one(
        "stock.location",
        string="Location",
        readonly=True,
    )

    product_id = fields.Many2one(
        "product.product",
        readonly=True,
    )

    content_qty = fields.Float(
        string="On Hand",
        digits="Product Unit of Measure",
        readonly=True,
    )

    location_package_count = fields.Integer(
        string="Packages in Location",
        readonly=True,
    )

    location_package_capacity = fields.Integer(
        string="Location Capacity",
        readonly=True,
    )

    @api.model
    def action_open(self):
        locations = self.env["stock.location"]._find_underfilled_package_locations()
        packages = self.env["stock.package"].search(
            [("location_id", "in", locations.ids), ("can_be_consolidated", "=", True)]
        )
        lines = self.create(
            [
                {
                    "package_id": package.id,
                    "package_location_id": package.location_id.id,
                    "product_id": package.package_product_id.id,
                    "content_qty": package.content_qty,
                    "location_package_count": package.location_id.package_count,
                    "location_package_capacity": (package.location_id.package_capacity),
                }
                for package in packages
            ]
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Locations to Consolidate"),
            "res_model": self._name,
            "view_mode": "list",
            "views": [
                (
                    self.env.ref(
                        "stock_warehouse_consolidation"
                        ".consolidation_location_line_view_list"
                    ).id,
                    "list",
                )
            ],
            "domain": [("id", "in", lines.ids)],
            "context": {"group_by": ["product_id"]},
            "target": "current",
            "help": self.env._(
                "<p class='o_view_nocontent_smiling_face'>Nothing to"
                " consolidate</p><p>No location currently holds fewer packages"
                " than its storage category allows.</p>"
            ),
        }

    def action_relocate(self):
        packages = self.package_id
        if not packages:
            raise UserError(self.env._("Select at least one package to relocate."))
        return packages.action_open_relocation_wizard()
