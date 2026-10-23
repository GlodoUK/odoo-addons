import re

from odoo import api, fields, models, tools

_NOT_ALNUM = re.compile(r"[^0-9A-Z]")


class ResPartnerStateFromZipPrefix(models.Model):
    _name = "res_partner_state_from_zip.prefix"
    _description = "Zip Prefix to State"
    _order = "country_id, prefix"
    _rec_name = "prefix"

    prefix = fields.Char(
        required=True,
        help="Upper case, letters and digits only. Longest match wins.",
    )
    state_id = fields.Many2one(
        "res.country.state", required=True, ondelete="cascade", index=True
    )
    country_id = fields.Many2one(related="state_id.country_id", store=True, index=True)

    _prefix_uniq = models.Constraint(
        "unique(country_id, prefix)",
        "A zip prefix can only map to one state per country!",
    )

    @api.model
    def _clean(self, value):
        return _NOT_ALNUM.sub("", (value or "").upper())

    @api.model
    def _zip_key(self, country, zip_code):
        key = self._clean(zip_code)
        reduce = getattr(self, f"_zip_key_{country.code.lower()}", None)
        return reduce(key) if reduce else key

    @api.model
    def _zip_key_gb(self, key):
        # Drop the inward code, else B1 1AA (B11AA) hits the B11 rule.
        return key[:-3] if len(key) >= 5 else key

    @api.model
    @tools.ormcache("country_id")
    def _prefix_map(self, country_id):
        rows = self.sudo().search_read(
            [("country_id", "=", country_id)], ["prefix", "state_id"]
        )
        return {row["prefix"]: row["state_id"][0] for row in rows}

    @api.model
    def _state_id_for_zip(self, country, zip_code):
        prefixes = self._prefix_map(country.id)
        if not prefixes:
            return False
        key = self._zip_key(country, zip_code)
        for length in range(len(key), 0, -1):
            state_id = prefixes.get(key[:length])
            if state_id:
                return state_id
        return False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "prefix" in vals:
                vals["prefix"] = self._clean(vals["prefix"])
        records = super().create(vals_list)
        self.env.registry.clear_cache()
        return records

    def write(self, vals):
        if "prefix" in vals:
            vals["prefix"] = self._clean(vals["prefix"])
        res = super().write(vals)
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res
