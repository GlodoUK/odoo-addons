from collections import defaultdict

from odoo import api, models
from odoo.tools import str2bool

FALLBACK_PARAM = "res_partner_state_from_zip.fallback_company_country"


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners.action_fill_state_from_zip()
        return partners

    def write(self, vals):
        res = super().write(vals)
        # Not on state_id, so a hand-cleared state sticks.
        if "zip" in vals or "country_id" in vals:
            self.action_fill_state_from_zip()
        return res

    @api.model
    def _state_from_zip_use_company_country(self):
        return str2bool(
            self.env["ir.config_parameter"].sudo().get_param(FALLBACK_PARAM, "False"),
            default=False,
        )

    def _state_from_zip_country(self, use_company_country):
        self.ensure_one()
        if self.country_id or not use_company_country:
            return self.country_id
        return (self.company_id or self.env.company).country_id

    @api.onchange("zip", "country_id")
    def _onchange_zip_fill_state(self):
        if self.env.context.get("skip_res_partner_state_from_zip"):
            return
        if self.state_id or not self.zip:
            return
        country = self._state_from_zip_country(
            self._state_from_zip_use_company_country()
        )
        if not country:
            return
        state_id = self.env["res_partner_state_from_zip.prefix"]._state_id_for_zip(
            country, self.zip
        )
        if state_id:
            self.country_id = country
            self.state_id = state_id

    def action_fill_state_from_zip(self):
        # _update_address skips the address sync, which would push the guess
        # onto the parent or children.
        if self.env.context.get("skip_res_partner_state_from_zip"):
            return
        Prefix = self.env["res_partner_state_from_zip.prefix"]
        use_company_country = self._state_from_zip_use_company_country()
        by_address = defaultdict(list)
        for partner in self:
            country = partner._state_from_zip_country(use_company_country)
            if partner.state_id or not partner.zip or not country:
                continue
            state_id = Prefix._state_id_for_zip(country, partner.zip)
            if state_id:
                by_address[state_id, country.id].append(partner.id)
        for (state_id, country_id), partner_ids in by_address.items():
            self.browse(partner_ids)._update_address(
                {"state_id": state_id, "country_id": country_id}
            )
