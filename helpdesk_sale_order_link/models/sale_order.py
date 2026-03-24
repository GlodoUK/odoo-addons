from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    helpdesk_tickets_ids = fields.Many2many(
        "helpdesk.ticket",
        "helpdesk_ticket_sale_order_rel",
    )

    helpdesk_tickets_count = fields.Integer(
        compute="_compute_helpdesk_tickets_count",
        store=True,
    )

    @api.depends("helpdesk_tickets_ids")
    def _compute_helpdesk_tickets_count(self):
        for order in self:
            order.helpdesk_tickets_count = len(order.helpdesk_tickets_ids)

    def action_view_ticket_ids(self):
        helpdesk_tickets_ids = self.mapped("helpdesk_tickets_ids").ids

        action = {
            "res_model": "helpdesk.ticket",
            "type": "ir.actions.act_window",
        }

        if len(helpdesk_tickets_ids) == 1:
            action.update(
                {
                    "res_id": helpdesk_tickets_ids[0],
                    "view_mode": "form",
                }
            )

        else:
            action.update(
                {
                    "domain": [("id", "in", helpdesk_tickets_ids)],
                    "view_mode": "list,form",
                }
            )

        return action
