from odoo import fields, models


class ProductAttributeCpqGroup(models.Model):
    _name = "product.attribute.cpq.group"
    _description = "Product Attribute CPQ Group"
    _order = "sequence, id"

    active = fields.Boolean(
        default=True,
    )

    name = fields.Char(
        required=True,
    )

    sequence = fields.Integer(
        default=10,
    )

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if "name" not in default:
            for group, vals in zip(self, vals_list, strict=False):
                vals["name"] = self.env._("%s (copy)", group.name)
        return vals_list
