from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    commingled_ok = fields.Boolean(
        "Is Commingled?",
    )

    commingled_ids = fields.One2many(
        "product.commingled",
        "parent_product_id",
        "Commingled Products",
        copy=False,
    )

    used_in_commingled_ids = fields.One2many(
        "product.commingled",
        "product_id",
        copy=False,
    )

    @api.constrains("company_id", "product_variant_ids")
    def _check_commingled_company(self):
        # Ensure that the commingled products are all in the same company
        for record in self:
            for line in record.commingled_ids:
                if (
                    line.product_id.company_id and record.company_id
                ) and line.product_id.company_id != record.company_id:
                    raise ValidationError(
                        _(
                            "Commingled products must be in the company same as"
                            " the parent product"
                        )
                    )
            for line in record.used_in_commingled_ids:
                if (
                    line.product_id.company_id and record.company_id
                ) and line.parent_product_id.company_id != record.company_id:
                    raise ValidationError(
                        _(
                            "Commingled products must be in the company same as"
                            " the parent product"
                        )
                    )
