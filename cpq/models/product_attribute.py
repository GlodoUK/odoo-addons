from odoo import _, api, fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"
    _order = "sequence"

    active = fields.Boolean(
        default=True,
    )
    cpq_propagate_to_variant = fields.Boolean(
        string="Propagate to the Variant",
        default=True,
    )

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if "name" not in default:
            default["name"] = _("%s (copy)") % (self.name)
        return super().copy(default=default)


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    active = fields.Boolean(
        default=True,
    )
    cpq_custom_type = fields.Selection(
        [
            ("integer", "Integer"),
            ("float", "Float"),
            ("char", "Text"),
            ("many2one", "Many2one"),
        ],
        string="Configurable custom type",
    )

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if "name" not in default:
            default["name"] = _("%s (copy)") % (self.name)
        return super().copy(default=default)

    def _cpq_cast_custom(self, value):
        """
        Cast the stored custom_value into the real value.
        i.e. custom_value may store a int, which we need to cast into an Odoo
        record
        """
        self.ensure_one()

        if not self.is_custom or not self.cpq_custom_type:
            return value

        method = f"_cpq_cast_custom_{self.cpq_custom_type}"
        return getattr(self, method)(value)

    def _cpq_cast_custom_integer(self, value):
        return self._cpq_sanitise_custom_integer(value)

    def _cpq_cast_custom_float(self, value):
        return self._cpq_sanitise_custom_integer(value)

    def _cpq_cast_custom_char(self, value):
        return self._cpq_sanitise_custom_char(value)

    def _cpq_cast_custom_many2one(self, _value):
        return NotImplementedError()

    def _cpq_sanitise_custom(self, value):
        self.ensure_one()

        if not self.is_custom or not self.cpq_custom_type:
            return value

        method = f"_cpq_sanitise_custom_{self.cpq_custom_type}"
        return getattr(self, method)(value)

    def _cpq_sanitise_custom_integer(self, value):
        return int(value)

    def _cpq_sanitise_custom_float(self, value):
        return float(value)

    def _cpq_sanitise_custom_char(self, value):
        if value is None:
            return ""
        return value.strip()

    def _cpq_sanitise_custom_many2one(self, value):
        raise NotImplementedError()

    def _cpq_validate_custom(self, value):
        self.ensure_one()

        if not self.is_custom or not self.cpq_custom_type:
            return True

        method = f"_cpq_validate_custom_{self.cpq_custom_type}"
        return getattr(self, method)(value)

    def _cpq_validate_custom_integer(self, value):
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    def _cpq_validate_custom_float(self, value):
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _cpq_validate_custom_char(self, value):
        return isinstance(value, str) and len(value) > 0

    def _cpq_validate_custom_many2one(self, value):
        raise NotImplementedError()


class ProductAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"
    _order = "product_tmpl_id, sequence, id"

    sequence = fields.Integer(default=10)
    cpq_propagate_to_variant = fields.Boolean(
        related="attribute_id.cpq_propagate_to_variant", store=True
    )

    def _cpq_get_combination_info(self):
        self.ensure_one()
        i = self

        return {
            "id": i.id,
            "name": i.display_name,
            "display_type": i.attribute_id.display_type,
            "ptav_ids": [
                ptav_id._cpq_get_combination_info()
                for ptav_id in i.product_template_value_ids.filtered(
                    lambda l: l.ptav_active  # noqa: E741
                )
            ],
        }


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    cpq_propagate_to_variant = fields.Boolean(
        related="attribute_id.cpq_propagate_to_variant"
    )
    cpq_custom_type = fields.Selection(
        related="product_attribute_value_id.cpq_custom_type"
    )

    def _cpq_get_combination_info(self):
        self.ensure_one()
        ptav_id = self

        return {
            "id": ptav_id.id,
            "name": ptav_id.name,
            "html_color": ptav_id.html_color,
            "is_custom": ptav_id.is_custom,
            "price_extra": 0.0,
            "excluded": False,
            "cpq_custom_type": ptav_id.cpq_custom_type,
        }
