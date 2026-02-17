from odoo import api, fields, models


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    cpq_custom_type = fields.Selection(
        [
            ("char", "Text"),
            ("float", "Float"),
            ("integer", "Integer"),
        ],
        "Configurable Custom Type",
    )

    def _cpq_cast_custom(self, value):
        """
        Cast the stored custom_value into the real value.
        i.e. custom_value may store a int,
        which we need to cast into an Odoo record
        """
        self.ensure_one()

        if not self.is_custom or not self.cpq_custom_type:
            return value

        method = f"_cpq_cast_custom_{self.cpq_custom_type}"
        return getattr(self, method)(value)

    @api.model
    def _cpq_cast_custom_char(self, value):
        return self._cpq_sanitise_custom_char(value)

    @api.model
    def _cpq_cast_custom_float(self, value):
        return self._cpq_sanitise_custom_float(value)

    @api.model
    def _cpq_cast_custom_integer(self, value):
        return self._cpq_sanitise_custom_integer(value)

    def _cpq_sanitise_custom(self, value):
        self.ensure_one()

        if not self.is_custom or not self.cpq_custom_type:
            return value

        method = f"_cpq_sanitise_custom_{self.cpq_custom_type}"
        return getattr(self, method)(value)

    @api.model
    def _cpq_sanitise_custom_char(self, value):
        if not value:
            return ""
        return value.strip()

    @api.model
    def _cpq_sanitise_custom_float(self, value):
        return float(value)

    @api.model
    def _cpq_sanitise_custom_integer(self, value):
        return int(value)

    def _cpq_validate_custom(self, value):
        self.ensure_one()

        if not self.is_custom or not self.cpq_custom_type:
            return True

        method = f"_cpq_validate_custom_{self.cpq_custom_type}"
        return getattr(self, method)(value)

    @api.model
    def _cpq_validate_custom_char(self, value):
        return isinstance(value, str) and value.strip()

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
    def _cpq_validate_custom_integer(self, value):
        if isinstance(value, bool):
            return False
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
