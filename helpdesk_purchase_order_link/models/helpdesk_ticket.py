from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    purchase_ids = fields.Many2many(
        comodel_name="purchase.order",
        relation="helpdesk_ticket_purchase_order_rel",
        context={"active_test": False},
    )

    purchase_ids_count = fields.Integer(
        compute="_compute_purchase_ids_count",
        store=True,
    )

    @api.depends("purchase_ids")
    def _compute_purchase_ids_count(self):
        for ticket in self:
            ticket.purchase_ids_count = len(ticket.purchase_ids)

    def action_view_purchase_ids(self):
        self.ensure_one()

        purchase_ids = self.mapped("purchase_ids").ids

        action = {
            "res_model": "purchase.order",
            "type": "ir.actions.act_window",
        }

        if len(purchase_ids) == 1:
            action.update(
                {
                    "res_id": purchase_ids[0],
                    "view_mode": "form",
                }
            )

        else:
            action.update(
                {
                    "domain": [("id", "in", purchase_ids)],
                    "view_mode": "tree,form",
                }
            )

        return action
