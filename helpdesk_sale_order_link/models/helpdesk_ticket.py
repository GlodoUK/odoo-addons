from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    so_ids = fields.Many2many(
        "sale.order",
        "helpdesk_ticket_sale_order_rel",
        string="Quotations",
        context={"active_test": False},
    )

    sale_ids_count = fields.Integer(
        compute="_compute_sale_ids_count",
        store=True,
    )

    @api.depends("so_ids")
    def _compute_sale_ids_count(self):
        for ticket in self:
            ticket.sale_ids_count = len(ticket.so_ids)

    def action_view_sale_ids(self):
        sale_order_ids = self.mapped("so_ids").ids

        action = {
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
        }

        if len(sale_order_ids) == 1:
            action.update(
                {
                    "res_id": sale_order_ids[0],
                    "view_mode": "form",
                }
            )

        else:
            action.update(
                {
                    "domain": [("id", "in", sale_order_ids)],
                    "view_mode": "list,form",
                }
            )

        return action
