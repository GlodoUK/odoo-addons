from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..tools import normalize_domain


class ResPartnerEmailDomainBan(models.Model):
    _name = "res.partner.email.domain.ban"
    _description = "Banned Email Domain"
    _order = "name"

    name = fields.Char(
        string="Domain",
        required=True,
        help="Bare domain name, e.g. gmail.com. Do not include an '@', a "
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
    active = fields.Boolean(
        default=True,
        help="Archive rather than delete an entry you do not want: deleted "
        "entries shipped with the module come back on the next upgrade.",
    )

    _unique_domain_normalized = models.Constraint(
        "UNIQUE (domain_normalized)",
        "This domain is already banned.",
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
                    "as gmail.com, without an '@', a local part or a URL.",
                    domains=", ".join(invalid.mapped("name")),
                )
            )
