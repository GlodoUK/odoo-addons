from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    sale_explode = fields.Selection(
        selection=[("ask", "Ask"), ("always", "Always")],
        string="Explode on Sale Orders",
        help="Offer (Ask) or automatically perform (Always) the explosion of"
        " this kit into its components on sale order lines."
        " Leave empty to never explode on sale orders.",
    )

    @api.constrains("sale_explode", "type")
    def _check_sale_mrp_phantom_explode(self):
        invalid = self.filtered(lambda x: x.sale_explode and x.type != "phantom")
        if invalid:
            raise ValidationError(
                self.env._(
                    "You can only enable the explode feature if there's a Phantom / Kit"
                    " to explode"
                )
            )
