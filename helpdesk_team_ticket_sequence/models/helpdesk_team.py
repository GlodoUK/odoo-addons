from odoo import _, fields, models
from odoo.exceptions import UserError


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    ticket_sequence_id = fields.Many2one(
        "ir.sequence",
    )

    def set_sequence_to_tickets_wo_number(self):
        """Sets ticket number for every ticket according to set sequence in team"""
        for obj in self:
            if not obj.ticket_sequence_id:
                raise UserError(
                    _("Please, set up Ticket Sequence for '%(obj_name)s'")
                    % {"obj_name": obj.name}
                )
            for ticket_id in obj.ticket_ids:
                if ticket_id.number == "/" or not ticket_id.number:
                    ticket_id.number = obj.ticket_sequence_id._next()
