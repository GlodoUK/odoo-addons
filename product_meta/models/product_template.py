from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    type = fields.Selection(selection_add=[("meta", "Meta Product")])

    detailed_type = fields.Selection(
        selection_add=[("meta", "Meta Product")], ondelete={"meta": "set default"}
    )

    meta_product_tmpl_line_ids = fields.One2many(
        "product.template.meta.line",
        "parent_id",
    )

    @api.onchange("type")
    def _onchange_meta_type(self):
        if self.type != "meta":
            return

        self.purchase_ok = False

    @api.constrains("type", "purchase_ok", "attribute_line_ids")
    def _ensure_meta_type(self):
        for record in self:
            if record.type != "meta":
                return

            if record.purchase_ok:
                raise ValidationError(_("You cannot purchase a meta product"))

            if not record.meta_product_tmpl_line_ids:
                raise ValidationError(
                    _("You need at least 1 child product within a meta product")
                )

            if record.attribute_line_ids:
                raise ValidationError(_("Meta products cannot have attributes"))
