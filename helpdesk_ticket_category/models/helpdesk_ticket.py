from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_categ_id = fields.Many2one(
        "helpdesk.ticket.category",
        "Category",
        tracking=True,
    )

    def _sla_find(self):
        result = {}

        for ticket, sla_items in super()._sla_find().items():
            result[ticket] = sla_items.filtered(
                lambda s, ticket=ticket: (
                    not s.ticket_categ_ids
                    or (ticket.ticket_categ_id & s.ticket_categ_ids)
                )
            )

        return result
