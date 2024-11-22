from odoo import api, fields, models

from odoo.addons.phone_validation.tools import phone_validation


class ResPartner(models.Model):
    _inherit = "res.partner"

    extra_phone_ids = fields.One2many("res.partner.extra.phone", "partner_id")


class ResPartnerExtraPhone(models.Model):
    _name = "res.partner.extra.phone"
    _description = "Partner Extra Phone Number"
    _order = "sequence asc"
    _rec_name = "phone"

    sequence = fields.Integer(default=10)
    partner_id = fields.Many2one("res.partner", required=True)
    type = fields.Selection(
        [
            ("phone", "Phone"),
            ("mobile", "Mobile"),
            ("personal", "Personal"),
            ("emergency", "Emergency"),
            ("out_of_hours", "Out of Hours"),
            ("ddi", "Direct Dial"),
            ("other", "Other"),
        ],
        default="phone",
        required=True,
    )
    phone = fields.Char(required=True)

    @api.onchange("phone", "partner_id")
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self._phone_format(self.phone)

    def _phone_format(self, number, country=None, company=None):
        country = country or self.partner_id.country_id or self.env.company.country_id
        if not country:
            return number

        return phone_validation.phone_format(
            number,
            country.code if country else None,
            country.phone_code if country else None,
            force_format="INTERNATIONAL",
            raise_exception=False,
        )
