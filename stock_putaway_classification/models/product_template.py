from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Mirror of the variant field for the single-variant case, the same idiom
    # as product.template.default_code. Multi-variant templates set it per
    # variant instead.
    product_classification_id = fields.Many2one(
        "product.classification",
        string="Classification",
        compute="_compute_product_classification_id",
        inverse="_inverse_product_classification_id",
        help="Value/volume classification (e.g. from Netstock). Put-away "
        "rules with a classification only apply to matching products.",
    )

    @api.depends("product_variant_ids.product_classification_id")
    def _compute_product_classification_id(self):
        for template in self:
            variants = template.product_variant_ids
            template.product_classification_id = (
                variants.product_classification_id if len(variants) == 1 else False
            )

    def _inverse_product_classification_id(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.product_classification_id = (
                    template.product_classification_id
                )
