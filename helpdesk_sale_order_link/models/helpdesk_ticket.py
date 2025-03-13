from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    so_ids = fields.Many2many(
        comodel_name="sale.order",
        relation="helpdesk_ticket_sale_order_rel",
        context={"active_test": False},
        string="Quotations",
    )
    sale_ids_count = fields.Integer(compute="_compute_sale_ids_count", store=True)

    @api.depends("so_ids")
    def _compute_sale_ids_count(self):
        for record in self:
            record.sale_ids_count = len(record.so_ids)

    def action_view_sale_ids(self):
        sale_order_ids = self.mapped("so_ids").ids
        action = {
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
        }
        if len(sale_order_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": sale_order_ids[0],
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", sale_order_ids)],
                    "view_mode": "tree,form",
                }
            )
        return action
