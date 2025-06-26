from markupsafe import Markup

from odoo import _, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    merged_into = fields.Many2one(
        "helpdesk.ticket",
        help="The ticket into which this ticket was merged.",
        readonly=True,
    )

    def merge_into(
        self,
        target_ticket,
        merge_description=True,
        merge_chatter=True,
        merge_attachments=True,
        merge_activities=True,
        merge_followers=True,
        merge_tags=True,
        merge_priority=True,
    ):
        self.ensure_one()

        if self.partner_id != target_ticket.partner_id:
            raise ValueError(_("You cannot merge tickets from different customers."))

        target_ticket.message_post(
            body=Markup(
                _(
                    "Ticket "
                    "<a href='#' data-oe-model='helpdesk.ticket' "
                    "data-oe-id='%(ticket_id)s'>%(ticket_name)s</a>"
                    " was merged into this ticket",
                    ticket_id=self.id,
                    ticket_name=self.name,
                )
            )
        )

        # Merge Description
        if merge_description:
            description = self.description
            if description and description.strip() != "":
                target_ticket.write(
                    {
                        "description": f"{target_ticket.description}\n\n=== Merged from ticket {self.id} ({self.name}) ===\n\n{description}"  # noqa: E501
                    }
                )

        # Merge chatter
        if merge_chatter:
            for message in self.message_ids:
                message.write(
                    {
                        "res_id": target_ticket.id,
                        "subject": f"Merged from Ticket {self.id}: {self.name}",
                    }
                )

        # Merge attachments
        if merge_attachments:
            attachment_ids = self.env["ir.attachment"].search(
                [("res_model", "=", "helpdesk.ticket"), ("res_id", "=", self.id)]
            )
            for attachment in attachment_ids:
                attachment.sudo().write({"res_id": target_ticket.id})

        # Merge activities
        if merge_activities:
            for activity in self.activity_ids:
                activity.write({"res_id": target_ticket.id})
            target_ticket.activity_ids |= self.activity_ids

        # Merge Followers

        if merge_followers:
            for follower in self.message_follower_ids:
                if follower.partner_id not in target_ticket.message_follower_ids.mapped(
                    "partner_id"
                ):
                    target_ticket.message_subscribe(
                        partner_ids=[follower.partner_id.id]
                    )

        # Merge Tags
        if merge_tags:
            target_ticket.tag_ids |= self.tag_ids

        # Merge Priority
        if merge_priority:
            if int(self.priority or "0") > int(target_ticket.priority or "0"):
                target_ticket.write({"priority": self.priority})

        self.message_post(
            body=Markup(
                _(
                    "This ticket was merged into "
                    "<a href='#' data-oe-model='helpdesk.ticket' "
                    "data-oe-id='%(ticket_id)s'>%(ticket_name)s</a>",
                    ticket_id=target_ticket.id,
                    ticket_name=target_ticket.name,
                )
            )
        )
        self.write(
            {
                "active": False,
                "merged_into": target_ticket.id,
            }
        )
        return True
