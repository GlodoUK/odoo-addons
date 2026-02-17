from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    cpq_preset = fields.Boolean()

    cpq_combination_indices = fields.Char(
        "Configurable Combination Indices",
        compute="_compute_cpq_combination_indices",
        index=True,
        store=True,
    )

    cpq_custom_combination_indices = fields.Char(
        "Configurable Custom Value Indices",
        compute="_compute_cpq_combination_indices",
        index=True,
        store=True,
    )

    cpq_custom_value_ids = fields.One2many(
        "product.product.cpq.custom.value",
        "product_id",
        "Configurable Custom Values",
        readonly=True,
    )

    @api.depends(
        "cpq_custom_value_ids.hash",
        "product_template_attribute_value_ids"
    )
    def _compute_cpq_combination_indices(self):
        for product in self:
            if not product.cpq_ok:
                product.cpq_combination_indices = False
                product.cpq_custom_combination_indices = False
                continue

            product.cpq_combination_indices = (
                product.product_template_attribute_value_ids._ids2str()
            )
            product.cpq_custom_combination_indices = (
                product.cpq_custom_value_ids._ids2str()
            )

    @api.depends(
        "cpq_ok",
        "product_template_attribute_value_ids",
    )
    def _compute_combination_indices(self):
        with_cpq = self.filtered(lambda p: p.cpq_ok)
        res = super(ProductProduct, self - with_cpq)._compute_combination_indices()
        for product in with_cpq:
            # TODO should this include the cpq_custom_value_ids somehow?
            # This would make our lives easier
            product.combination_indices = False
        return res

    def _compute_display_name(self):
        super()._compute_display_name()

        for record in self.sudo().filtered(lambda p: p.cpq_ok):
            # Find the original calculated variant name, and then string replace
            # it with custom value info
            original_variant_name = (
                record.product_template_attribute_value_ids._get_combination_name()
            )

            custom_info_dict = {
                i.ptav_id: i.display_name for i in record.cpq_custom_value_ids
            }

            variant_combination = []
            for ptav_id in record.product_template_attribute_value_ids:
                if not ptav_id.is_custom or not custom_info_dict.get(ptav_id):
                    variant_combination.append(ptav_id._get_combination_name())
                    continue

                variant_combination.append(custom_info_dict.get(ptav_id))

            if original_variant_name:
                record.display_name = record.display_name.replace(
                    original_variant_name, ", ".join(variant_combination)
                )

    def _cpq_combination_tuples(self):
        self.ensure_one()

        data = []

        custom_info_dict = {i.ptav_id.id: i for i in self.cpq_custom_value_ids}

        for ptav_id in self.product_template_attribute_value_ids:
            if not ptav_id.is_custom or not custom_info_dict.get(ptav_id.id):
                data.append((ptav_id, None))
                continue

            custom_value_id = custom_info_dict.get(ptav_id.id)
            value = ptav_id.product_attribute_value_id._cpq_cast_custom(
                custom_value_id.custom_value
            )

            data.append((ptav_id, value))

        return data
