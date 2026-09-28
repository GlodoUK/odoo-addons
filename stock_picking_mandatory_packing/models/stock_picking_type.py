from odoo import api, fields, models
from odoo.exceptions import ValidationError

VALID_TYPES = ["incoming", "outgoing", "internal"]


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    must_be_packed = fields.Boolean(default=False)

    @api.constrains("must_be_packed", "code")
    def _ensure_must_be_packed_is_safe(self):
        invalid = self.filtered(
            lambda x: x.code not in VALID_TYPES and x.must_be_packed
        )
        if invalid:
            raise ValidationError(
                self.env._(
                    "'Must be packed' can only be set on one of the following types:"
                    " %(types)s",
                    types=", ".join(VALID_TYPES),
                )
            )
