from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    helpdesk_ticket_ids = fields.Many2many(
        comodel_name="helpdesk.ticket",
        relation="helpdesk_ticket_purchase_order_rel",
    )

    ticket_count = fields.Integer(
        compute="_compute_ticket_count",
        store=True,
    )

    @api.depends("helpdesk_ticket_ids")
    def _compute_ticket_count(self):
        for order in self:
            order.ticket_count = len(order.helpdesk_ticket_ids)

    def action_view_helpdesk_ticket_ids(self):
        self.ensure_one()

        helpdesk_ticket_ids = self.mapped("helpdesk_ticket_ids").ids

        action = {
            "res_model": "helpdesk.ticket",
            "type": "ir.actions.act_window",
        }

        if len(helpdesk_ticket_ids) == 1:
            action.update(
                {
                    "res_id": helpdesk_ticket_ids[0],
                    "view_mode": "form",
                }
            )

        else:
            action.update(
                {
                    "domain": [("id", "in", helpdesk_ticket_ids)],
                    "view_mode": "list,form",
                }
            )

        return action
