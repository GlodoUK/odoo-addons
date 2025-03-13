from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    number = fields.Char(default="/", readonly=True, copy=False, required=True)

    def return_ticket_sequence_id(self, vals):
        if vals.get("team_id"):
            is_no_number = not vals.get("number") or vals.get("number") == "/"
            team_id = self.env["helpdesk.team"].sudo().browse(vals.get("team_id"))
            if is_no_number and team_id and team_id.ticket_sequence_id:
                return team_id.ticket_sequence_id._next()
            if team_id:
                raise UserError(
                    _("Please, set Ticket Sequence for %(team)s")
                    % {"team": team_id.name}
                )
        raise UserError(_("Team should be assigned to ticket."))

    @api.model
    def create(self, vals):
        vals["number"] = self.return_ticket_sequence_id(vals)
        res = super().create(vals)
        return res

    def name_get(self):
        result = []
        for ticket in self:
            name = "%s (#%d)" % (ticket.name, ticket._origin.id)

            if ticket.number != "/":
                name = "%s (%s)" % (ticket.name, ticket.number)

            result.append((ticket.id, name))
        return result
