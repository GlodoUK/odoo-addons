from odoo import api, fields, models


class SaleOrderHelpdeskLink(models.Model):
    _inherit = "sale.order"

    # TODO remove helpdesk_ticket_id in next versions
    #  migration acted out, so we can do it in two steps:
    #  step1: migrate to '15.0.1.0.2' with new fields
    #  step2: remove helpdesk_ticket_id field on next version

    helpdesk_ticket_id = fields.Many2one("helpdesk.ticket", index=True)
    helpdesk_tickets_ids = fields.Many2many(
        comodel_name="helpdesk.ticket",
        relation="helpdesk_ticket_sale_order_rel",
        string="Helpdesk Tickets",
    )

    helpdesk_tickets_count = fields.Integer(
        compute="_compute_helpdesk_tickets_count", store=True
    )

    @api.depends("helpdesk_tickets_ids")
    def _compute_helpdesk_tickets_count(self):
        for record in self:
            record.helpdesk_tickets_count = len(record.helpdesk_tickets_ids)

    def action_view_ticket_ids(self):
        helpdesk_tickets_ids = self.mapped("helpdesk_tickets_ids").ids
        action = {
            "res_model": "helpdesk.ticket",
            "type": "ir.actions.act_window",
        }
        if len(helpdesk_tickets_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": helpdesk_tickets_ids[0],
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", helpdesk_tickets_ids)],
                    "view_mode": "tree,form",
                }
            )
        return action
