from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"
    _order = "sequence"

    cpq_propagate_to_variant = fields.Boolean(
        "Propagate To Variant",
        default=True,
    )
    cpq_attribute_group_id = fields.Many2one(
        "cpq.attribute.group",
        string="Configurator Group",
    )

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if "name" not in default:
            for attribute, vals in zip(self, vals_list, strict=False):
                vals["name"] = self.env._("%s (copy)", attribute.name)
        return vals_list


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    cpq_custom_type = fields.Selection(
        [
            ("integer", "Integer"),
            ("float", "Float"),
            ("char", "Text"),
        ],
        "Configurable Custom Type",
    )

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if "name" not in default:
            for value, vals in zip(self, vals_list, strict=False):
                vals["name"] = self.env._("%s (copy)", value.name)
        return vals_list

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
        return self._cpq_sanitise_custom_float(value)

    def _cpq_cast_custom_char(self, value):
        return self._cpq_sanitise_custom_char(value)

    def _cpq_sanitise_custom(self, value):
        self.ensure_one()

        if not self.is_custom or not self.cpq_custom_type:
            return value

        method = f"_cpq_sanitise_custom_{self.cpq_custom_type}"
        return getattr(self, method)(value)

    @api.model
    def _cpq_sanitise_custom_integer(self, value):
        return int(value)

    @api.model
    def _cpq_sanitise_custom_float(self, value):
        return float(value)

    @api.model
    def _cpq_sanitise_custom_char(self, value):
        if not value:
            return ""
        return value.strip()

    def _cpq_validate_custom(self, value):
        self.ensure_one()

        if not self.is_custom or not self.cpq_custom_type:
            return True

        method = f"_cpq_validate_custom_{self.cpq_custom_type}"
        return getattr(self, method)(value)

    @api.model
    def _cpq_validate_custom_integer(self, value):
        if isinstance(value, bool):
            return False
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    @api.model
    def _cpq_validate_custom_float(self, value):
        if isinstance(value, bool):
            return False
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @api.model
    def _cpq_validate_custom_char(self, value):
        return isinstance(value, str) and value.strip()


class ProductTemplateAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    cpq_propagate_to_variant = fields.Boolean(
        related="attribute_id.cpq_propagate_to_variant", store=True
    )

    def _cpq_get_combination_info(self):
        self.ensure_one()
        i = self

        group = i.attribute_id.cpq_attribute_group_id
        return {
            "id": i.id,
            "name": i.display_name,
            "display_type": i.attribute_id.display_type,
            "group_id": group.id or False,
            "group_name": group.name or False,
            "group_sequence": group.sequence if group else 9999,
            "ptav_ids": [
                ptav_id._cpq_get_combination_info()
                for ptav_id in i.product_template_value_ids.filtered(
                    lambda attr_line: attr_line.ptav_active
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
