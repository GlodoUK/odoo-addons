import logging
import re

from odoo import api, fields, models

_logger = logging.getLogger(__file__)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    custom_display_name_format = fields.Text(
        "Custom Display Name",
        help="Custom Display format to use for this address. Useful to reformat a bank"
        "account for a specific region without making lots of manual changes to invoice"
        "documents.\n\n"
        "You can use python-style string pattern"
        "(for example, use '%(acc_number)s' to display the field 'account number') plus"
        "\n%(bank_name)s: the name of the bank"
        "\n%(bank_bic)s: the bank identifier code",
    )

    custom_display_name_format_warning = fields.Char(
        compute="_compute_custom_display_name_format_warning"
    )

    def _get_custom_display_name_format_values(self):
        self.ensure_one()
        return {
            "acc_number": self.acc_number or "",
            "bank_name": self.bank_id.name or "",
            "bank_bic": self.bank_bic or "",
            "bank_street": self.bank_id.street or "",
            "bank_street2": self.bank_id.street2 or "",
            "bank_city": self.bank_id.city or "",
            "bank_state": self.bank_id.state.name or "",
            "bank_country": self.bank_id.country.name or "",
            "bank_country_code": self.bank_id.country.code or "",
            "bank_zip": self.bank_id.zip or "",
            "currency_name": self.currency_id.name or "",
            "currency_full_name": self.currency_id.full_name or "",
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
        if self.env.context.get("display_account_trust"):
            trusted_label = (
                self.env._("trusted")
                if self.allow_out_payment
                else self.env._("untrusted")
            )
            name = f"{name} {trusted_label}"
        name = re.sub(r"\s\s+", " ", name)
        return name

    @api.depends("custom_display_name_format")
    @api.depends_context("display_account_trust")
    def _compute_display_name(self):
        res = super()._compute_display_name()

        for record in self.filtered(lambda x: x.custom_display_name_format):
            try:
                record.display_name = record._get_custom_display_name_format()
            except KeyError as e:
                _logger.warning("Failed to compute custom display name", e)
                pass

        return res
