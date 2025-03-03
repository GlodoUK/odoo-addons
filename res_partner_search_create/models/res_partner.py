from odoo import api, models

REMAP_FIELDS = {"state": "state_id", "country": "country_id"}


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def search_create(self, vals, **kwargs):
        # vals are expected to to be in the format supplied to
        # self.env['res.partner'].create call

        search = kwargs.get(
            "search_using",
            {"zip": "ilike", "name": "=ilike", "parent_id": "=", "type": "="},
        )

        # Attempt to translate country into country_id
        country = None
        search_country_name = vals.pop("country", None)
        if search_country_name:
            country = self.env["res.country"].search(
                [
                    "|",
                    ("code_alpha3", "=", search_country_name),
                    ("code", "=", search_country_name),
                ],
                limit=1,
            )

        if not country:
            country = self.env["res.company"]._company_default_get().country_id

        vals.update({"country_id": country.id})

        # attempt to convert state into state_id
        search_state_name = vals.pop("state", None)
        if country and search_state_name:
            state = self.env["res.country.state"].search(
                [
                    ("name", "=ilike", search_state_name),
                    ("country_id", "=", country.id),
                ],
                limit=1,
            )

            vals.update({"state_id": state.id})

        # any fields to remap in search_using
        # i.e. country to country_id
        for k, v in REMAP_FIELDS.items():
            if k in search:
                operator = search.pop(k)
                search.update({v: operator})

        search_domain = []
        for field, operator in search.items():
            search_domain.append((field, operator or "=", vals.get(field, False)))

        partner_id = self.search(search_domain, limit=1)

        if not partner_id:
            return self.create(vals)

        if kwargs.get("update", False):
            partner_id.write(vals)

        return partner_id
