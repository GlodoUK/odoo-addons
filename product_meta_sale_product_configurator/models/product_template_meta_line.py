from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplateMetaLine(models.Model):
    _inherit = "product.template.meta.line"

    mode = fields.Selection(
        selection_add=[("configurator", "Configurable")],
        ondelete={"configurator": "cascade"},
    )

    child_tmpl_valid_attr_value_ids = fields.Many2many(
        "product.template.attribute.value",
        domain="[('product_tmpl_id', '=', child_tmpl_id)]",
        ondelete="cascade",
        string="Valid Attributes",
    )

    @api.onchange("mode", "child_tmpl_id")
    def onchange_child_tmpl_id(self):
        res = super().onchange_child_tmpl_id()

        if self.mode == "attribute_combination" and self.child_variant_id:
            self.child_variant_id = False

        return res

    def _get_child_product_variant_configurator(self, **kwargs):
        # FIXME add combination filtering based on
        # self.child_tmpl_valid_attr_value_ids

        line = kwargs.get("line", self.env["sale.order.line"])

        if line.meta_attrs:
            product_id = line.meta_attrs.get(f"{self.id}", {}).get("product_id")

            if product_id:
                return self.env["product.product"].browse(product_id)

        return self.child_tmpl_id._create_first_product_variant()

    def _get_sale_order_line_vals(self, line):
        self.ensure_one()

        vals = super()._get_sale_order_line_vals(line)

        custom_values = (
            line.meta_attrs.get(f"{self.id}", {}).get("product_custom_attribute_values")
            or []
        )

        # save is_custom attributes values
        if custom_values:
            vals["product_custom_attribute_value_ids"] = [
                (
                    0,
                    0,
                    {
                        "custom_product_template_attribute_value_id": custom_value[
                            "custom_product_template_attribute_value_id"
                        ],
                        "custom_value": custom_value["custom_value"],
                    },
                )
                for custom_value in custom_values
            ]

        return vals

    @api.constrains("mode", "child_tmpl_valid_attr_value_ids")
    def _ensure_child_tmpl_valid_attrs_set(self):
        broken = self.filtered(
            lambda m: m.mode == "configurator" and not m.child_tmpl_valid_attr_value_ids
        )
        if broken:
            raise ValidationError(
                _(
                    "Meta product must have some valid attributes "
                    "set when mode is configurator"
                )
            )
