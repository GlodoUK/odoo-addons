from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    validate_before_send_to_shipper = fields.Boolean(default=True)

    def _ensure_valid_shipping(self, pickings):
        self.ensure_one()
        if not self.validate_before_send_to_shipper:
            return
        method_name = f"_{self.delivery_type}_ensure_valid_shipping"
        if hasattr(self, method_name):
            return getattr(self, method_name)(pickings)
