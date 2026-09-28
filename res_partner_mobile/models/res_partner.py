from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    mobile = fields.Char()

    @api.onchange("mobile", "country_id", "company_id")
    def _onchange_mobile_validation(self):
        # This is done in onchange to keep consistent with phone_validation
        # phone and mobile validation
        if self.mobile and hasattr(self, "_phone_format"):
            self.mobile = (
                self._phone_format(fname="mobile", force_format="INTERNATIONAL")
                or self.mobile
            )
