from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplateMetaLine(models.Model):
    _name = "product.template.meta.line"
    _description = "Product Template Meta Line"

    parent_id = fields.Many2one(
        "product.template",
        required=True,
        index=True,
        ondelete="cascade",
        domain="[('type', '=', 'meta')]",
    )
    mode = fields.Selection(
        [
            ("specific", "Variant"),
        ],
        default="specific",
        required=True,
    )
    child_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        index=True,
        domain="[('type', '!=', 'meta')]",
        ondelete="cascade",
        string="Product",
    )
    child_variant_id = fields.Many2one(
        "product.product",
        domain="[('product_tmpl_id', '=', child_tmpl_id)]",
        ondelete="cascade",
        string="Specific Variant",
    )
    quantity = fields.Float(required=True, default=1)
    uom_id = fields.Many2one(related="child_tmpl_id.uom_id")

    @api.onchange("mode", "child_tmpl_id")
    def onchange_child_tmpl_id(self):
        if self.mode == "specific" and (
            not self._origin or self._origin.child_tmpl_id != self.child_tmpl_id
        ):
            self.child_variant_id = fields.first(self.child_tmpl_id.product_variant_ids)

    def _get_child_product_variant(self, **kwargs):
        """
        Get or create the variant, according to the combination or optionally
        default to the "first".
        """
        self.ensure_one()
        method = getattr(self, f"_get_child_product_variant_{self.mode}")
        return method(**kwargs)

    def _get_child_product_variant_specific(self, **kwargs):
        self.ensure_one()
        return self.child_variant_id

    @api.constrains("parent_id", "child_variant_id")
    def _ensure_no_recursion(self):
        for record in self:
            if record.parent_id == record.child_tmpl_id:
                raise ValidationError(_("Cannot have recursive meta products"))

            if record.parent_id.type != "meta":
                raise ValidationError(
                    _("Meta child must have a meta product as the parent!")
                )

            if record.child_tmpl_id.type == "meta":
                raise ValidationError(_("Cannot have a meta product as a child!"))

    @api.constrains("child_tmpl_id", "child_variant_id", "mode")
    def _ensure_related_variant(self):
        for record in self.filtered(lambda line: line.mode == "specific"):
            if record.child_tmpl_id != record.child_variant_id.product_tmpl_id:
                raise ValidationError(_("You cannot have unrelated variant"))
