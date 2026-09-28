from odoo import api, fields, models
from odoo.tools.mail import parse_contact_from_email

from ..tools import normalize_domain


class ResPartner(models.Model):
    _inherit = "res.partner"

    email_domain_ids = fields.One2many(
        "res.partner.email.domain",
        "partner_id",
        string="Email Domains",
        help="Domains this contact is known by. A contact emailing in from one "
        "of them is filed under this contact. A domain may only be listed "
        "against one contact.",
    )

    @api.model
    def _get_partner_per_email_domain(self, emails):
        """Map each email to the partner that claims its domain.

        Keys are derived exactly as '_find_or_create_from_emails' derives the
        keys of its 'additional_values', so that the two line up.

        :return: {email key: partner id}, omitting emails whose domain is
          unclaimed, banned or not a domain at all.
        :rtype: dict
        """
        domain_per_key = {}
        for email in emails:
            key = parse_contact_from_email(email)[1]
            domain = normalize_domain(key.rpartition("@")[2]) if key else False
            if domain:
                domain_per_key[key] = domain
        if not domain_per_key:
            return {}

        domains = set(domain_per_key.values())
        # Bans are applied here and not only when a domain is assigned: a domain
        # banned after the fact then stays inert, rather than mis-filing every
        # sender who happens to share it.
        banned = set(
            self.env["res.partner.email.domain.ban"]
            .sudo()
            .search([("domain_normalized", "in", list(domains))])
            .mapped("domain_normalized")
        )
        domains -= banned
        if not domains:
            return {}

        partner_per_domain = {
            record.domain_normalized: record.partner_id.id
            for record in self.env["res.partner.email.domain"]
            .sudo()
            .search([("domain_normalized", "in", list(domains))])
        }
        return {
            key: partner_per_domain[domain]
            for key, domain in domain_per_key.items()
            if domain in partner_per_domain
        }

    @api.model
    def _find_or_create_from_emails(self, emails, additional_values=None, **kwargs):
        """Nest partners created from an email under the owner of its domain.

        This is the single funnel every mail-created partner passes through, so
        overriding it covers the mail gateway, Discuss recipients and mail
        template recipients alike. 'additional_values' only reaches partners
        that are actually created, so existing contacts are never re-parented.
        """
        partner_per_key = self._get_partner_per_email_domain(emails)
        if partner_per_key:
            additional_values = {
                key: dict(values) for key, values in (additional_values or {}).items()
            }
            parents = self.browse(set(partner_per_key.values())).sudo()
            company_per_parent = {parent.id: parent.company_id.id for parent in parents}
            for key, partner_id in partner_per_key.items():
                values = additional_values.setdefault(key, {})
                # An explicit parent from the calling record wins: crm passes the
                # lead's commercial partner, which beats a guess from the domain.
                if values.get("parent_id"):
                    continue
                # Do not file a contact belonging to one company under another
                # company's partner.
                company_id = values.get("company_id")
                parent_company_id = company_per_parent.get(partner_id)
                if company_id and parent_company_id and company_id != parent_company_id:
                    continue
                values["parent_id"] = partner_id
        return super()._find_or_create_from_emails(
            emails, additional_values=additional_values, **kwargs
        )
