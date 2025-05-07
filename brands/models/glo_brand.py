from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GloBrand(models.Model):
    _name = "glo.brand"
    _description = "Brand"
    _order = "name"

    name = fields.Char(
        required=True,
    )

    active = fields.Boolean(
        default=True,
    )

    is_default = fields.Boolean(
        string="Default Brand",
    )

    logo = fields.Binary(
        string="Brand Logo",
    )

    partner_id = fields.Many2one(
        "res.partner",
        required=True,
    )

    country_id = fields.Many2one(
        related="partner_id.country_id",
        store=True,
    )

    state_id = fields.Many2one(
        related="partner_id.state_id",
        store=True,
    )

    city = fields.Char(
        related="partner_id.city",
        store=True,
    )

    email = fields.Char(
        related="partner_id.email",
        store=True,
    )

    phone = fields.Char(
        related="partner_id.phone",
        store=True,
    )

    street = fields.Char(
        related="partner_id.street",
        store=True,
    )

    street2 = fields.Char(
        related="partner_id.street2",
        store=True,
    )

    vat = fields.Char(
        related="partner_id.vat",
        store=True,
    )

    website = fields.Char(
        related="partner_id.website",
        store=True,
    )

    zip = fields.Char(
        related="partner_id.zip",
        store=True,
    )

    report_header = fields.Html(
        string="Tagline",
        help="Printed in the header of reports.",
    )

    report_footer = fields.Html(
        string="Document Footer",
        help="Printed in the footer of reports.",
    )

    @api.constrains("is_default")
    def _constrains_is_default(self):
        count = self.search_count([("is_default", "=", True)])
        if count > 1:
            msg = _("There can only be one default brand!")
            raise ValidationError(msg)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        self.ensure_one()
        self.name = self.partner_id.name

    @api.model
    def get_default_record(self):
        domain = [("is_default", "=", True)]
        return self.env["glo.brand"].search(domain, limit=1)
