from odoo import _, fields, models
from odoo.exceptions import ValidationError


class MergeTicketWizard(models.TransientModel):
    _name = "helpdesk.ticket.merge.wizard"
    _description = "Helpdesk Ticket Merge Wizard"

    ticket_ids = fields.Many2many(
        "helpdesk.ticket",
        string="Tickets to Merge",
        default=lambda self: self._default_ticket_ids(),
    )
    target_ticket_id = fields.Many2one(
        "helpdesk.ticket",
        string="Destination Ticket",
        default=lambda self: self._default_target_ticket(),
    )

    merge_description = fields.Boolean(
        help="If checked, merge ticket descriptions into the destination ticket.",
        default=True,
    )
    merge_chatter = fields.Boolean(
        help="If checked, merged ticket chatter into the destination ticket.",
        default=True,
    )
    merge_attachments = fields.Boolean(
        help="If checked, merge ticket attachments into the destination ticket.",
        default=True,
    )
    merge_activities = fields.Boolean(
        help="If checked, merge ticket activities into the destination ticket.",
        default=True,
    )
    merge_followers = fields.Boolean(
        help="If checked, merge ticket followers into the destination ticket.",
        default=True,
    )
    merge_tags = fields.Boolean(
        help="If checked, merge ticket tags into the destination ticket.",
        default=True,
    )
    merge_priority = fields.Boolean(
        help=(
            "If checked, destination ticket is set to the highest priority of the"
            " merged tickets."
        ),
        default=True,
    )

    def _default_target_ticket(self):
        return self.env["helpdesk.ticket"].browse(self._context.get("active_ids"))[0]

    def _default_ticket_ids(self):
        tickets = self.env["helpdesk.ticket"].browse(self._context.get("active_ids"))
        if len(tickets.mapped("partner_id")) > 1:
            raise ValidationError(_("You can't merge tickets from multiple customers!"))
        return tickets

    def action_merge_tickets(self):
        self.ensure_one()
        for ticket in self.ticket_ids.filtered(
            lambda t: t.id != self.target_ticket_id.id
        ):
            ticket.merge_into(
                self.target_ticket_id,
                merge_description=self.merge_description,
                merge_chatter=self.merge_chatter,
                merge_attachments=self.merge_attachments,
                merge_activities=self.merge_activities,
                merge_followers=self.merge_followers,
                merge_tags=self.merge_tags,
                merge_priority=self.merge_priority,
            )
        load_ticket_id = self.target_ticket_id.id
        return {
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.ticket",
            "view_mode": "form",
            "res_id": load_ticket_id,
        }
