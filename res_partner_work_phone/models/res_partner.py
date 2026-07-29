from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    work_number = fields.Char()
    work_number_ext = fields.Char()

    @api.onchange("work_number", "country_id", "company_id")
    def _onchange_mobile_validation(self):
        # This is done in onchange to keep consistent with phone_validation
        # phone and mobile validation
        if self.work_number and hasattr(self, "_phone_format"):
            self.work_number = (
                self._phone_format(fname="work_number", force_format="INTERNATIONAL")
                or self.work_number
            )
