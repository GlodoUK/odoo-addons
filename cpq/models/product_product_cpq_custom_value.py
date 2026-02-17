import hashlib

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductProductCpqCustomValue(models.Model):
    _name = "product.product.cpq.custom.value"
    _description = "Product Variant CPQ Custom Value"
    _order = "ptav_id, id"

    _product_ptav_uniq = models.Constraint(
        "UNIQUE(product_id, ptav_id)",
        "Duplicate CPQ custom value!",
    )

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )

    custom_value = fields.Char()

    hash = fields.Char(
        compute="_compute_hash",
        index=True,
        store=True,
    )

    product_id = fields.Many2one(
        "product.product",
        index=True,
        ondelete="cascade",
        required=True,
    )

    ptav_id = fields.Many2one(
        "product.template.attribute.value",
        "Attribute Value",
        index=True,
        ondelete="restrict",
        required=True,
    )

    # ruff: noqa: E501
    @api.constrains("ptav_id")
    def _ensure_ptav_propagate_to_variant(self):
        if self.filtered(lambda v: not v.ptav_id.cpq_propagate_to_variant):
            msg = self.env._("Cannot store custom values for attributes not marked as Propagate To Variant")
            raise ValidationError(msg)

    @api.depends("custom_value", "ptav_id.display_name")
    def _compute_name(self):
        for value in self:
            value.name = f"{value.ptav_id.display_name}: {value.custom_value}"

    @api.depends("custom_value", "ptav_id")
    def _compute_hash(self):
        for value in self:
            value.hash = self._generate_hash(value.ptav_id, value.custom_value)

    @api.model
    def _generate_hash(self, ptav_id, custom_value):
        return "{}/{}".format(
            ptav_id.id, hashlib.sha1(str(custom_value).encode("utf-8")).hexdigest()
        )

    def _ids2str(self):
        return ",".join(sorted(self.mapped("hash")))
