from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_variant_exclusion_ids = fields.One2many(
        "product.variant.exclusion", "tmpl_id"
    )

    def _filter_combinations_impossible_by_config(
        self, combination_tuples, ignore_no_variant=False
    ):
        res = super()._filter_combinations_impossible_by_config(
            combination_tuples, ignore_no_variant=ignore_no_variant
        )
        exclusions = self.product_variant_exclusion_ids
        yield from [
            combination
            for combination in res
            if not any(
                all(ptav in combination for ptav in ex.ptav_ids) for ex in exclusions
            )
        ]


class ProductVariantExclusion(models.Model):
    _name = "product.variant.exclusion"
    _description = "Product Variant Exclusion"

    tmpl_id = fields.Many2one(
        "product.template", required=True, index=True, ondelete="cascade"
    )
    ptav_ids = fields.Many2many(
        "product.template.attribute.value",
        "product_variant_exclusion_ptav_rel",
        domain="[('product_tmpl_id', '=', tmpl_id), ('attribute_id.create_variant', '!=', 'no_variant')]",  # noqa: E501
        string="Combination to Exclude",
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for tmpl_id in records.mapped("tmpl_id"):
            tmpl_id._create_variant_ids()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(k in ("tmpl_id", "ptav_ids") for k in vals.keys()):
            for tmpl_id in self.mapped("tmpl_id"):
                tmpl_id._create_variant_ids()
        return res

    def unlink(self):
        tmpl_ids = self.mapped("tmpl_id")
        res = super().unlink()
        for tmpl_id in tmpl_ids:
            tmpl_id._create_variant_ids()
        return res

    @api.constrains("ptav_ids", "tmpl_id")
    def _check_ptavs(self):
        for record in self:
            seen = self.env["product.attribute"]

            if not record.ptav_ids:
                raise ValidationError(
                    _("At least 1 product template attribute value is required!")
                )

            for ptav_id in record.ptav_ids:
                if record.tmpl_id != ptav_id.product_tmpl_id:
                    raise ValidationError(
                        _(
                            "Product template attribute value does belong to product"
                            " template"
                        )
                    )

                if ptav_id.attribute_id in seen:
                    raise ValidationError(
                        _(
                            "Duplicate attribute '%(name)s' found",
                            name=ptav_id.attribute_id.name,
                        )
                    )
                seen |= ptav_id.attribute_id
