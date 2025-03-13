from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_categ_id = fields.Many2one(
        "helpdesk.ticket.category",
        string="Category",
        tracking=True,
    )

    @api.model
    def _sla_reset_trigger(self):
        return super()._sla_reset_trigger() + ["ticket_categ_id"]

    def _sla_find(self):
        result = {}

        for ticket, sla_items in super()._sla_find().items():
            result[ticket] = sla_items.filtered(
                lambda s: not s.ticket_categ_ids
                or (ticket.ticket_categ_id & s.ticket_categ_ids)  # noqa: B023
            )

        return result
