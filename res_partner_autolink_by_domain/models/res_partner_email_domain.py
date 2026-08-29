from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..tools import normalize_domain


class ResPartnerEmailDomain(models.Model):
    _name = "res.partner.email.domain"
    _description = "Partner Email Domain"
    _order = "name"

    name = fields.Char(
        string="Domain",
        required=True,
        help="Bare domain name, e.g. example.com. Do not include an '@', a "
        "local part or a URL.",
    )
    # Not required=True: Odoo leaves stored computed fields out of the INSERT and
    # fills them in a later recompute pass, so a NOT NULL column would reject
    # every create, valid or not.
    domain_normalized = fields.Char(
        string="Normalized Domain",
        compute="_compute_domain_normalized",
        store=True,
        index=True,
        help="Lowercased and IDNA encoded form of the domain. This is what an "
        "incoming email address is matched against.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        required=True,
        index=True,
        ondelete="cascade",
    )

    # Deliberately unique across every partner rather than per partner: a domain
    # that resolves to two contacts cannot identify either of them.
    _unique_domain_normalized = models.Constraint(
        "UNIQUE (domain_normalized)",
        "This domain is already assigned to another contact.",
    )

    @api.depends("name")
    def _compute_domain_normalized(self):
        for record in self:
            record.domain_normalized = normalize_domain(record.name)

    @api.constrains("domain_normalized")
    def _check_domain_normalized(self):
        invalid = self.filtered(lambda record: not record.domain_normalized)
        if invalid:
            raise ValidationError(
                self.env._(
                    "%(domains)s: not a valid domain. Give a bare domain such "
                    "as example.com, without an '@', a local part or a URL.",
                    domains=", ".join(invalid.mapped("name")),
                )
            )
        banned = (
            self.env["res.partner.email.domain.ban"]
            .sudo()
            .search([("domain_normalized", "in", self.mapped("domain_normalized"))])
            .mapped("domain_normalized")
        )
        if banned:
            raise ValidationError(
                self.env._(
                    "%(domains)s: banned domains, shared by senders who have "
                    "nothing to do with each other, so they cannot identify a "
                    "single contact.",
                    domains=", ".join(banned),
                )
            )
