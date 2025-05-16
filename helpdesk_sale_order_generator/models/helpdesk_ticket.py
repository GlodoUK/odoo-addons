from odoo import _, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    def generate_so_with_prefilled_data(self):
        return {
            "name": _("New Sale Order"),
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_partner_id": self.partner_id.id if self.partner_id else False,
                "default_helpdesk_tickets_ids": [self.id],
            },
        }
