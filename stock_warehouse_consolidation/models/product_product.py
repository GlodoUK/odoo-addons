from odoo import models
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_consolidate_group(self):
        self.ensure_one()

        candidates = self.env["stock.package"]._find_consolidation_candidates()
        packages = candidates.filtered(lambda p: p.package_product_id == self)

        if len(packages) < 2:
            raise UserError(
                self.env._(
                    "%(product)s no longer has two packages that can be merged.",
                    product=self.display_name,
                )
            )

        return packages.action_open_consolidation_wizard()

    def action_relocate_group(self):
        self.ensure_one()

        locations = self.env["stock.location"]._find_underfilled_package_locations()
        packages = self.env["stock.package"].search(
            [
                ("location_id", "in", locations.ids),
                ("can_be_consolidated", "=", True),
                ("package_product_id", "=", self.id),
            ]
        )

        if not packages:
            raise UserError(
                self.env._(
                    "%(product)s no longer has packages in underfilled locations.",
                    product=self.display_name,
                )
            )

        return packages.action_open_relocation_wizard()
