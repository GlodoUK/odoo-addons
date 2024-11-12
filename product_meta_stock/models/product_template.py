from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.onchange("type")
    def _onchange_meta_type(self):
        res = super()._onchange_meta_type()

        self.route_ids = False

        return res

    @api.constrains("type", "route_ids")
    def _ensure_meta_type_stock(self):
        for record in self.filtered(lambda p: p.type == "meta"):
            if record.route_ids:
                raise ValidationError(_("Meta products do not support routes!"))
