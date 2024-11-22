import re

from odoo import _, api, fields, models


class ResPartnerSocialMediaProvider(models.Model):
    _name = "res.partner.social.media.provider"
    _description = "Social Media Type"
    _inherits = {"res.partner": "partner_id"}

    partner_id = fields.Many2one("res.partner", required=True, index=True)
    font_awesome = fields.Char()
    url_format = fields.Char()
    extract_regex = fields.Char()

    @api.model
    def _extract_provider_and_account_from_url(self, url):
        for record in self.search([("extract_regex", "!=", False)]):
            matches = re.match(record.extract_regex, url)
            if matches:
                return (record, matches.groupdict().get("account"))

        return (False, False)

    def _get_website_and_link_for_account(self, account):
        self.ensure_one()

        if not self.url_format or not account:
            return (False, False)

        url = self.url_format.format(account=account)

        link = '<a href="{url}" target="_blank"><i class="{css}"></i> {account}</a>'.format(  # noqa: E501
            url=url,
            css=self.font_awesome,
            account=account,
        )

        return (
            url,
            link,
        )


class ResPartnerSocialMedia(models.Model):
    _name = "res.partner.social.media"
    _description = "Partner Social Media"

    type = fields.Selection(
        [
            ("auto", "Auto"),
            ("manual", "Manual"),
        ],
        default="auto",
        compute="_compute_type",
        inverse="_inverse_type",
        string="Mode",
    )

    partner_id = fields.Many2one("res.partner", required=True)
    provider_id = fields.Many2one(
        "res.partner.social.media.provider",
        required=True,
    )
    image_128 = fields.Binary(related="provider_id.image_128")
    image_256 = fields.Binary(related="provider_id.image_256")
    image_512 = fields.Binary(related="provider_id.image_512")
    image_1024 = fields.Binary(related="provider_id.image_1024")
    image_1920 = fields.Binary(related="provider_id.image_1920")
    account = fields.Char(required=True)
    website = fields.Char(
        compute="_compute_website",
        inverse="_inverse_website",
    )
    link = fields.Html(compute="_compute_website")

    def _compute_type(self):
        for record in self:
            if record.account and record.provider_id:
                record.type = "manual"
            else:
                record.type = "auto"

    def _inverse_type(self):
        pass

    def _inverse_website(self):
        for record in self:
            if not record.website:
                record.account = False
                record.link = False
                continue

            provider_id, account = self.env[
                "res.partner.social.media.provider"
            ]._extract_provider_and_account_from_url(record.website)
            if not provider_id or not account:
                record.account = False
                record.link = False
                continue

            record.account = account
            record.provider_id = provider_id

    @api.depends("account", "provider_id")
    def _compute_website(self):
        for record in self:
            if not record.provider_id:
                record.website = False
                record.link = False
                continue

            website, link = record.provider_id._get_website_and_link_for_account(
                record.account
            )

            record.website = website
            record.link = link

    @api.onchange("website")
    def _onchange_website(self):
        if not self.website:
            return

        model = self.env["res.partner.social.media.provider"]

        provider_id, account = model._extract_provider_and_account_from_url(
            self.website
        )

        if provider_id and account:
            self.provider_id = provider_id
            self.account = account
        else:
            return {
                "warning": {
                    "title": "Invalid URL",
                    "message": _(
                        "The URL you entered is not valid for any of the"
                        " configured social media providers (%s)"
                    )
                    % (", ".join(model.search([]).mapped("display_name"))),
                }
            }

    @api.model
    def create(self, vals):
        if not vals.get("provider_id") and vals.get("website"):
            provider_id, account = self.env[
                "res.partner.social.media.provider"
            ]._extract_provider_and_account_from_url(vals.get("website"))

            if provider_id and account:
                vals["provider_id"] = provider_id.id
                vals["account"] = account

        return super().create(vals)
