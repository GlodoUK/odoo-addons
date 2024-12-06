import hashlib

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductAttributeCustomValue(models.Model):
    _name = "product.product.cpq.custom.value"
    _description = "Product Variant CPQ Custom Value"
    _order = "ptav_id, id"

    name = fields.Char(compute="_compute_name", store=True)
    product_id = fields.Many2one(
        "product.product",
        index=True,
        required=True,
        ondelete="cascade",
    )
    ptav_id = fields.Many2one(
        "product.template.attribute.value",
        string="Attribute Value",
        required=True,
        ondelete="restrict",
        index=True,
    )
    custom_value = fields.Char()
    hash = fields.Char(compute="_compute_hash", store=True, index=True)

    @api.depends("ptav_id.display_name", "custom_value")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.ptav_id.display_name}: {record.custom_value}"

    @api.depends("ptav_id", "custom_value")
    def _compute_hash(self):
        for record in self:
            record.hash = self._generate_hash(record.ptav_id, record.custom_value)

    @api.model
    def _generate_hash(self, ptav_id, custom_value):
        return "{}/{}".format(
            ptav_id.id, hashlib.sha1(str(custom_value).encode("utf-8")).hexdigest()
        )

    def _ids2str(self):
        return ",".join(sorted(self.mapped("hash")))

    @api.constrains("ptav_id")
    def _ensure_ptav_propagate_to_variant(self):
        if self.filtered(lambda v: not v.ptav_id.cpq_propagate_to_variant):
            raise ValidationError(
                _(
                    "Attempting to propagate variant to custom values, however"
                    " it is marked as no propagate"
                )
            )

    _sql_constraints = [
        (
            "product_ptav_uniq",
            "unique (product_id, ptav_id)",
            "Duplicate CPQ custom value",
        ),
    ]


class ProductProduct(models.Model):
    _inherit = "product.product"

    cpq_preset = fields.Boolean()
    cpq_custom_value_ids = fields.One2many(
        "product.product.cpq.custom.value",
        "product_id",
        readonly=True,
        string="Configurable Custom Values",
    )
    cpq_combination_indices = fields.Char(
        compute="_compute_cpq_combination_indices",
        store=True,
        index=True,
        string="Configurable Combination Indices",
    )
    cpq_custom_combination_indices = fields.Char(
        compute="_compute_cpq_combination_indices",
        store=True,
        index=True,
        string="Configurable Custom Value Indices",
    )

    @api.depends("cpq_custom_value_ids.hash", "product_template_attribute_value_ids")
    def _compute_cpq_combination_indices(self):
        for record in self:
            if not record.cpq_ok:
                record.cpq_combination_indices = False
                record.cpq_custom_combination_indices = False
                continue

            record.cpq_combination_indices = (
                record.product_template_attribute_value_ids._ids2str()
            )
            record.cpq_custom_combination_indices = (
                record.cpq_custom_value_ids._ids2str()
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

    @api.depends("cpq_custom_value_ids", "product_template_attribute_value_ids")
    def _compute_display_name(self):
        res = super()._compute_display_name()

        for record in self.sudo().filtered(lambda p: p.cpq_ok):
            # This was the least duplicate inducing version of this that I could
            # think of.

            # Find the original calculated variant name, and then string replace it
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

            record.display_name = record.display_name.replace(
                original_variant_name, ", ".join(variant_combination)
            )

        return res

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
