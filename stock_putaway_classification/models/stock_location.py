from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _check_can_be_used(self, product, quantity=0, package=None, location_qty=0):
        category = self.storage_category_id
        # Core caps only the package types a category lists; with
        # "Only Listed Package Types" any other type doesn't fit.
        if (
            category.only_listed_package_types
            and package
            and package.package_type_id
            and package.package_type_id
            not in category.package_capacity_ids.package_type_id
        ):
            return False
        # Core's "empty" only looks at quants, so two receipt lines can both be
        # put away into the same empty location before either is done.
        if category.allow_new_product == "empty" and self._has_pending_arrivals():
            return False
        return super()._check_can_be_used(
            product, quantity=quantity, package=package, location_qty=location_qty
        )

    def _has_pending_arrivals(self):
        self.ensure_one()
        return bool(
            self.env["stock.move.line"].search_count(
                [
                    (
                        "id",
                        "not in",
                        list(self.env.context.get("exclude_sml_ids", set())),
                    ),
                    ("location_dest_id", "=", self.id),
                    ("state", "not in", ("draft", "done", "cancel")),
                ],
                limit=1,
            )
        )
