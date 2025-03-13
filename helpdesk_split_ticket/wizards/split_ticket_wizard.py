import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SplitTicketWizard(models.TransientModel):
    _name = "split.ticket.wizard"

    message_id = fields.Many2one("mail.message")
    description = fields.Text()
    author_parent = fields.Many2one(
        "res.partner", related="message_id.author_id.parent_id"
    )

    followers = fields.Many2many("res.partner")
    followers_keep_old = fields.Boolean(default=True)
    followers_available_ids = fields.One2many(related="author_parent.child_ids")

    @api.model
    def default_get(self, inc_fields):
        res = super().default_get(inc_fields)
        if "message_id" in res:
            res["description"] = self.env["mail.message"].browse(res["message_id"]).body

        return res

    @api.onchange("message_id")
    def _onchange_message_id(self):
        self.description = self._remove_html_tags(self.message_id.body)

    @api.onchange("followers_keep_old")
    def _onchange_followers_keep_old(self):
        if not self.followers_keep_old and not self.author_parent:
            raise UserError(
                _(
                    "Message author does not have a parent company.\n"
                    "Recommended action: Use the same followers as "
                    "original message or fix the contact record and try again."
                )
            )

    def action_create_new_ticket(self):
        current_ticket = self.env["helpdesk.ticket"].browse(self.message_id.res_id)
        current_user = self.env.user

        # Keep current followers?
        followers_to_keep = None
        if self.followers_keep_old:
            followers_to_keep = current_ticket.message_follower_ids.filtered(
                lambda f: f.partner_id != current_user.partner_id
            )

        # Create new ticket
        new_ticket = self.env["helpdesk.ticket"].create(
            {
                "name": self._get_new_ticket_name(current_ticket),
                "description": self.description,
                "partner_id": self.message_id.author_id.id,
                "message_follower_ids": followers_to_keep
                if followers_to_keep
                else None,
            }
        )

        # Subscribe specified followers
        if self.followers:
            new_ticket.message_subscribe(self.followers.ids)

        # Visually link old ticket to the new one.
        current_ticket.message_post(
            type="notification",
            body=_(
                "New call <a href='#' data-oe-model='{model}' "
                "data-oe-id='{id}'>{number}</a> created from this ticket."
            ).format(
                model="helpdesk.ticket", id=new_ticket.id, number=new_ticket.number
            ),
        )
        return new_ticket

    def _get_new_ticket_name(self, current_ticket):
        return f"Ticket From {current_ticket.number}"

    def _remove_html_tags(self, text):
        comp = re.compile("<.*?>")
        return re.sub(comp, "", text)
