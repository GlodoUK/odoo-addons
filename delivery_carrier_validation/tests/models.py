from odoo import _, fields, models
from odoo.exceptions import UserError


class TestDeliveryMethod(models.Model):
    _inherit = "delivery.carrier"  # pylint: disable=R8180

    delivery_type = fields.Selection(
        selection_add=[("test", "Test")], ondelete={"test": "cascade"}
    )

    def _test_ensure_valid_shipping(self, pickings):
        raise UserError(_("Test"))
