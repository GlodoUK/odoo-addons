from odoo import fields, models
from odoo.fields import Domain


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    cpq_banding_relaxed_validation = fields.Boolean(
        "Relax Banding Validation",
        help="Allow a banding record to be moved between parents",
    )

    cpq_banding_id = fields.Many2one(
        "cpq.banding",
        "Banding",
        domain="[('is_leaf', '=', False)]",
    )

    cpq_custom_type = fields.Selection(
        selection_add=[
            ("banding", "Banding"),
        ]
    )

    def _cpq_sanitise_banding_domain(self, domain):
        self.ensure_one()

        if not self.cpq_banding_relaxed_validation:
            return Domain.AND(
                [
                    domain,
                    [
                        ("parent_id", "child_of", self.cpq_banding_id.id),
                        ("is_leaf", "=", True),
                    ],
                ]
            )

        return domain

    def _cpq_cast_custom_banding(self, value):
        try:
            return self.env["cpq.banding"].search(
                self._cpq_sanitise_banding_domain(
                    [
                        ("id", "=", int(value)),
                    ]
                )
            )
        except (ValueError, TypeError):
            return self.env["cpq.banding"]

    def _cpq_sanitise_custom_banding(self, value):
        try:
            return (
                self.env["cpq.banding"]
                .search(
                    self._cpq_sanitise_banding_domain(
                        [
                            ("id", "=", int(value)),
                        ]
                    )
                )
                .id
            )
        except (ValueError, TypeError):
            return False

    def _cpq_validate_custom_banding(self, value):
        try:
            value_as_int = int(value)
        except (ValueError, TypeError):
            return False

        count = self.env["cpq.banding"].search_count(
            self._cpq_sanitise_banding_domain(
                [
                    ("id", "=", value_as_int),
                ]
            )
        )
        return count == 1
