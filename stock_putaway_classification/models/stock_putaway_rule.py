from odoo import fields, models


class StockPutawayRule(models.Model):
    _inherit = "stock.putaway.rule"

    product_classification_id = fields.Many2one(
        "product.classification",
        string="Classification",
        ondelete="restrict",
        help="Only applies to products with this classification. The rule is "
        "skipped while the product already has stock in, or on its way to, "
        "the 'Store to' location, so each product keeps a single pick face.",
    )

    def _get_putaway_location(
        self, product, quantity=0, package=None, packaging=None, qty_by_location=None
    ):
        # Packages arrive with no product and their contents in the context.
        products = product or self.env.context.get("products", product)
        # Mixed classifications (or none) only match rules without one.
        classification = products.product_classification_id
        if len(classification) != 1 or len(products) != len(
            products.filtered("product_classification_id")
        ):
            classification = classification.browse()
        rules = self.filtered(
            lambda rule: (
                not rule.product_classification_id
                or (
                    rule.product_classification_id == classification
                    and not rule._is_product_stored(products)
                )
            )
        )
        # Core has already ordered the rules (package type > product >
        # category); a stable sort slots classification rules in after those
        # and ahead of the catch-alls.
        rules = rules.sorted(
            lambda rule: (
                bool(rule.package_type_ids),
                bool(rule.product_id),
                bool(rule.category_id),
                bool(rule.product_classification_id),
            ),
            reverse=True,
        )
        return super(StockPutawayRule, rules)._get_putaway_location(
            product,
            quantity=quantity,
            package=package,
            packaging=packaging,
            qty_by_location=qty_by_location,
        )

    def _is_product_stored(self, products):
        """Whether any of the products is on hand in, or being put away into,
        a location under this rule's 'Store to' location."""
        self.ensure_one()
        location = self.location_out_id
        if self.env["stock.quant"].search_count(
            [
                ("product_id", "in", products.ids),
                ("location_id", "child_of", location.id),
                ("quantity", ">", 0),
            ],
            limit=1,
        ):
            return True
        # Lines still aimed at the 'Store to' location itself haven't been put
        # away yet (including, outside _apply_putaway_strategy, the one being
        # placed now).
        return bool(
            self.env["stock.move.line"].search_count(
                [
                    (
                        "id",
                        "not in",
                        list(self.env.context.get("exclude_sml_ids", set())),
                    ),
                    ("product_id", "in", products.ids),
                    ("location_dest_id", "child_of", location.id),
                    ("location_dest_id", "!=", location.id),
                    ("state", "not in", ("draft", "done", "cancel")),
                ],
                limit=1,
            )
        )
