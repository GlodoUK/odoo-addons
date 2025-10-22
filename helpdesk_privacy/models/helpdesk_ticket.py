from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    is_private = fields.Boolean(
        "Private",
        help="Aside from internal staff, only the ticket creator, "
        "listed Customer and anyone added as a follower who is "
        "in the Customers organisation will be able "
        "to see/read the ticket.",
        tracking=True,
    )

    def _privacy_possible_followers(self):
        self.ensure_one()
        domain = self._privacy_possible_followers_domain()
        return self.env["res.partner"].search(domain)

    def _privacy_possible_followers_domain(self):
        self.ensure_one()

        return [
            ("id", "child_of", self.commercial_partner_id.id),
            ("id", "not in", self.message_partner_ids.ids),
        ]

    def message_update(self, msg_dict, update_vals=None):
        return super(
            HelpdeskTicket,
            self.with_context(
                helpdesk_privacy_only_subscribe_existing_partners=self.is_private
            ),
        ).message_update(msg_dict, update_vals=update_vals)

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        """
        Override to enforce privacy and prevent users from subscribing to tickets
        that they should not have access to.

        This can be achieved by unauthorised user responding to an email with Odoo
        headers on it. i.e. it is forwarded to them by someone who does have access.

        This is not a perfect implementation, but I'm unclear how to better handle
        better without a lot of "what-ifs":

        i.e. In the scenario User A who is following a private ticket CC's User B who is
        not, Odoo needs to accept the email, but we cannot just hard block the email as
        it should be posted. But we also can't just blackhole it.

        This then needs to handle BCC, etc.

        What I've chosen to do is accept the email, post it, but ensure that only the
        existing users are subscribed.

        This has the side effect of allowing parties without access the ability to
        potentially post message, but not be auto-subscribed.
        """
        if partner_ids and self.env.context.get(
            "helpdesk_privacy_only_subscribe_existing_partners"
        ):
            partner_ids = [i for i in partner_ids if i in self.message_partner_ids.ids]

        return super()._message_subscribe(
            partner_ids=partner_ids, subtype_ids=subtype_ids, customer_ids=customer_ids
        )
