from odoo import api, fields, models
from odoo.fields import Domain

# Bodies the web editor emits when nothing was typed.
EMPTY_BODIES = [False, "", "<p></p>", "<p><br></p>", "<p><br/></p>"]

# (model, partner field) pairs speculatively included in the feed. Models
# missing from the registry are skipped, so none of these are dependencies.
# Each has a matching source <filter> in mail_message_view_search_activity_feed.
FEED_DOCUMENT_MODELS = [
    ("crm.lead", "partner_id"),
    ("sale.order", "partner_id"),
    ("purchase.order", "partner_id"),
    ("account.move", "partner_id"),
    ("stock.picking", "partner_id"),
    ("helpdesk.ticket", "partner_id"),
]

# Lifecycle-event subtypes admitted into the feed even though their messages
# are tracking messages with blank bodies. Resolved with
# raise_if_not_found=False, so missing modules are simply skipped.
FEED_EVENT_SUBTYPES = [
    "sale.mt_order_sent",
    "sale.mt_order_confirmed",
    "purchase.mt_rfq_sent",
    "purchase.mt_rfq_confirmed",
    "purchase.mt_rfq_approved",
    "account.mt_invoice_validated",
    "account.mt_invoice_paid",
    "crm.mt_lead_won",
    "crm.mt_lead_lost",
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_commercial_partner = fields.Boolean(
        compute="_compute_is_commercial_partner",
    )

    @api.depends("commercial_partner_id")
    def _compute_is_commercial_partner(self):
        for partner in self:
            partner.is_commercial_partner = partner == partner.commercial_partner_id

    def _activity_feed_domains(self):
        """mail.message domains making up this partner's feed, OR'd together.

        Always evaluated on the commercial partner: the feed exists at the
        top level only and rolls up everything below it.

        Common document models are covered speculatively by
        FEED_DOCUMENT_MODELS; extend that list, or override this method for
        anything with different linkage::

            def _activity_feed_domains(self):
                domains = super()._activity_feed_domains()
                claims = self.env["repair.claim"].search(
                    [("customer_id", "child_of", self.id)]
                )
                domains.append(
                    [("model", "=", "repair.claim"), ("res_id", "in", claims.ids)]
                )
                return domains

        Build res_id lists with an ORM search as the current user so each
        source inherits that model's access rules; mail.message then applies
        its own access checks on top. To let users toggle the source, also
        add a ``<filter>`` on ``model`` to the feed search view
        (``mail_message_view_search_activity_feed``).
        """
        self.ensure_one()
        partners = self.env["res.partner"].search([("id", "child_of", self.id)])
        domains = [
            [("model", "=", "res.partner"), ("res_id", "in", partners.ids)],
        ]
        for model_name, partner_field in FEED_DOCUMENT_MODELS:
            if model_name not in self.env:
                continue
            records = self.env[model_name].search(
                [(partner_field, "child_of", self.id)]
            )
            domains.append([("model", "=", model_name), ("res_id", "in", records.ids)])
        return domains

    def _activity_feed_base_domain(self):
        """Filters applied to every source: no per-user notifications, no
        field-tracking messages, no automated log notes ("Sales Order
        created" and friends), no blank bodies unless there is an
        attachment. Lifecycle-event messages (FEED_EVENT_SUBTYPES) are
        admitted despite being blank-bodied tracking messages."""
        domain = Domain(
            [
                ("message_type", "!=", "user_notification"),
                ("tracking_value_ids", "=", False),
                # models with a _creation_subtype() post their creation
                # message with this marker div around the body
                ("body", "not like", 'summary="o_mail_notification"'),
                "|",
                ("attachment_ids", "!=", False),
                ("body", "not in", EMPTY_BODIES),
            ]
        )
        # _message_log* notes: creation logs on models without a creation
        # subtype, plus other machine chatter. Human "Log note" messages are
        # message_type "comment", so they survive; activity-done messages
        # use mail.mt_activities, so they survive too.
        mt_note_id = self.env["ir.model.data"]._xmlid_to_res_id(
            "mail.mt_note", raise_if_not_found=False
        )
        if mt_note_id:
            domain &= ~Domain(
                [
                    ("message_type", "=", "notification"),
                    ("subtype_id", "=", mt_note_id),
                ]
            )
        event_subtype_ids = [
            subtype.id
            for xmlid in FEED_EVENT_SUBTYPES
            if (subtype := self.env.ref(xmlid, raise_if_not_found=False))
        ]
        if event_subtype_ids:
            domain |= Domain("subtype_id", "in", event_subtype_ids)
        return domain

    def action_activity_feed(self):
        self.ensure_one()
        partner = self.commercial_partner_id
        domain = partner._activity_feed_base_domain() & Domain.OR(
            Domain(d) for d in partner._activity_feed_domains()
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._(
                "Activity Feed - %(partner)s", partner=partner.display_name
            ),
            "res_model": "mail.message",
            "view_mode": "kanban",
            "views": [
                (
                    self.env.ref(
                        "res_partner_activity_feed"
                        ".mail_message_view_kanban_activity_feed"
                    ).id,
                    "kanban",
                )
            ],
            "search_view_id": [
                self.env.ref(
                    "res_partner_activity_feed.mail_message_view_search_activity_feed"
                ).id
            ],
            "domain": list(domain),
            "context": {"create": False},
            "help": self.env._(
                "<p class='o_view_nocontent_smiling_face'>No activity yet</p>"
                "<p>Emails, notes and document activity for this partner "
                "will show up here.</p>"
            ),
        }
