import logging
import re

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    custom_display_name_format = fields.Text(
        "Custom Display Name",
        help="Custom Display format to use for this address. Useful to reformat a bank"
        "account for a specific region without making lots of manual changes to invoice"
        "documents.\n\n"
        "You can use python-style string pattern"
        "(for example, use '%(account_number)s' to display the field"
        " 'account number') plus"
        "\n%(bank_name)s: the name of the bank"
        "\n%(bank_bic)s: the bank identifier code",
    )

    custom_display_name_format_warning = fields.Char(
        compute="_compute_custom_display_name_format_warning"
    )

    def _get_custom_display_name_format_values(self):
        self.ensure_one()
        return {
            "account_number": self.account_number or "",
            # pre-20.0 key names, kept so existing formats keep working
            "acc_number": self.account_number or "",
            "bank_name": self.bank_name or "",
            "bank_bic": self.bank_bic or "",
            "bank_street": self.street or "",
            "bank_street2": self.street2 or "",
            "bank_city": self.city or "",
            "bank_state": self.state_id.name or "",
            "bank_country": self.country_id.name or "",
            "bank_country_code": self.country_id.code or "",
            "bank_zip": self.zip or "",
            # bank accounts no longer have a currency
            "currency_name": "",
            "currency_full_name": "",
            "partner_display_name": self.partner_id.display_name or "",
        }

    @api.depends("custom_display_name_format")
    def _compute_custom_display_name_format_warning(self):
        for record in self:
            if not record.custom_display_name_format:
                record.custom_display_name_format_warning = False
                continue

            try:
                _res = record._get_custom_display_name_format()
                record.custom_display_name_format_warning = False
            except KeyError as e:
                record.custom_display_name_format_warning = str(e)

    def _get_custom_display_name_format(self):
        self.ensure_one()
        name = (
            self.custom_display_name_format
            % self._get_custom_display_name_format_values()
        )
        name = re.sub(r"\s\s+", " ", name)
        return name

    @api.depends("custom_display_name_format")
    def _compute_display_name(self):
        res = super()._compute_display_name()

        for record in self.filtered(lambda x: x.custom_display_name_format):
            try:
                record.display_name = record._get_custom_display_name_format()
            except KeyError as e:
                _logger.warning("Failed to compute custom display name: %s", e)

        return res
