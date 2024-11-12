from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("type")
    def _ensure_not_meta(self):
        for record in self:
            if record.type == "meta":
                raise ValidationError(_("Product Variants cannot be a type of 'meta'"))
