from odoo import api, fields, models
from odoo.osv import expression


class ProductAttributeCustomValue(models.Model):
    _inherit = "product.product.cpq.custom.value"

    @api.depends("ptav_id.display_name", "custom_value")
    def _compute_name(self):
        res = super()._compute_name()
        # XXX: This is horrific. This needs to be sorted.
        for record in self.filtered(lambda v: v.ptav_id.cpq_custom_type == "banding"):
            banding_id = self.env["cpq.banding"].browse(int(record.custom_value))
            record.name = f"{record.ptav_id.display_name}: {banding_id.display_name}"
        return res


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    cpq_custom_type = fields.Selection(
        selection_add=[
            ("banding", "Banding"),
        ]
    )

    cpq_banding_id = fields.Many2one(
        comodel_name="cpq.banding",
        string="Banding",
        domain="[('is_leaf', '=', False)]",
    )

    cpq_banding_relaxed_validation = fields.Boolean(
        default=False,
        string="Relax Banding Validation",
        help="Allow a banding record to be moved between parents",
    )

    def _cpq_sanitise_banding_domain(self, domain):
        self.ensure_one()
        if not self.cpq_banding_relaxed_validation:
            return expression.AND(
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


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    cpq_banding_id = fields.Many2one(
        related="product_attribute_value_id.cpq_banding_id"
    )

    def _cpq_get_combination_info(self):
        res = super()._cpq_get_combination_info()
        if self.is_custom and self.cpq_custom_type == "banding":
            bandings = self.env["cpq.banding"].search(
                [
                    ("parent_id", "child_of", self.cpq_banding_id.id),
                    ("is_leaf", "=", True),
                ]
            )
            res.update(
                {
                    "cpq_selection_values": [
                        (banding.id, banding.display_name) for banding in bandings
                    ]
                }
            )

        return res
