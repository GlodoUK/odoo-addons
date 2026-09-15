from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.misc import formatLang

# Rail icons per document model; anything unknown gets a generic document
# icon. Extend alongside FEED_DOCUMENT_MODELS in res_partner.py.
FEED_ICONS = {
    "crm.lead": "fa-star-o",
    "sale.order": "fa-shopping-cart",
    "purchase.order": "fa-shopping-basket",
    "account.move": "fa-file-text-o",
    "stock.picking": "fa-truck",
    "helpdesk.ticket": "fa-life-ring",
}

# (amount field, currency field) shown next to feed cards of these models.
# Values are read at render time, i.e. they are the document's CURRENT
# amount, not the amount when the message was posted.
FEED_SUMMARIES = {
    "crm.lead": ("expected_revenue", "company_currency"),
    "sale.order": ("amount_total", "currency_id"),
    "purchase.order": ("amount_total", "currency_id"),
    "account.move": ("amount_total", "currency_id"),
}


class MailMessage(models.Model):
    _inherit = "mail.message"

    activity_feed_is_note = fields.Boolean(
        compute="_compute_activity_feed_is_note",
    )
    activity_feed_icon = fields.Char(
        compute="_compute_activity_feed_icon",
    )
    activity_feed_summary = fields.Char(
        compute="_compute_activity_feed_summary",
    )

    @api.depends("is_internal", "subtype_id.internal")
    def _compute_activity_feed_is_note(self):
        for message in self:
            message.activity_feed_is_note = bool(
                message.is_internal or message.subtype_id.internal
            )

    @api.depends("model", "res_id")
    def _compute_activity_feed_summary(self):
        self.activity_feed_summary = False
        by_model = defaultdict(list)
        for message in self:
            if message.model in FEED_SUMMARIES and message.res_id:
                by_model[message.model].append(message)
        for model_name, messages in by_model.items():
            if model_name not in self.env:
                continue
            amount_field, currency_field = FEED_SUMMARIES[model_name]
            records = self.env[model_name].browse(
                {message.res_id for message in messages}
            )
            try:
                summaries = {
                    record.id: formatLang(
                        self.env,
                        record[amount_field],
                        currency_obj=record[currency_field],
                    )
                    for record in records.exists()._filtered_access("read")
                }
            except AccessError:
                # a message can be readable while its document is not;
                # better an unadorned card than a broken view
                continue
            for message in messages:
                message.activity_feed_summary = summaries.get(message.res_id, False)

    @api.depends("model", "message_type", "is_internal", "subtype_id.internal")
    def _compute_activity_feed_icon(self):
        for message in self:
            if message.model and message.model != "res.partner":
                icon = FEED_ICONS.get(message.model, "fa-file-text-o")
            elif message.message_type in ("email", "email_outgoing"):
                icon = "fa-envelope-o"
            elif message.activity_feed_is_note:
                icon = "fa-pencil"
            else:
                icon = "fa-comments-o"
            message.activity_feed_icon = icon
