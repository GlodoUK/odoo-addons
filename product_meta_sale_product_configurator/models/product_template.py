from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    def _only_active_for_meta_line(self, meta_line_id):
        meta_line_id.ensure_one()

        return self._only_active().filtered(
            lambda v: v in meta_line_id.child_tmpl_valid_attr_value_ids
        )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    has_configurable_attributes = fields.Boolean(recursive=True)

    @api.depends(
        "type",
        "meta_product_tmpl_line_ids",
        "meta_product_tmpl_line_ids.child_tmpl_id.has_configurable_attributes",
    )
    def _compute_has_configurable_attributes(self):
        todo = self.filtered(lambda p: p.type == "meta")

        for product in todo:
            product.has_configurable_attributes = any(
                [
                    i.has_configurable_attributes
                    for i in product.meta_product_tmpl_line_ids.mapped("child_tmpl_id")
                ]
            )

        return super(
            ProductTemplate, self - todo
        )._compute_has_configurable_attributes()

    @api.constrains("optional_product_ids")
    def _ensure_optional_product_ids_not_meta(self):
        invalid = self.filtered(
            lambda p: p.optional_product_ids.mapped(lambda o: o.type == "meta")
        )
        if invalid:
            raise ValidationError(
                _("You cannot have a meta product as an optional product!")
            )
