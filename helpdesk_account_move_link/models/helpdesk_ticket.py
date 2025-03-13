from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    account_move_ids = fields.Many2many(
        "account.move",
        "account_move_helpdesk_ticket_rel",
        "helpdesk_ticket_id",
        "account_move_id",
    )
    account_move_count = fields.Integer(
        compute="_compute_account_move_count", store=True
    )

    @api.depends("account_move_ids")
    def _compute_account_move_count(self):
        for record in self:
            record.account_move_count = len(record.account_move_ids)

    def action_view_account_move_ids(self):
        account_move_ids = self.mapped("account_move_ids").ids
        action = {
            "res_model": "account.move",
            "type": "ir.actions.act_window",
        }
        if len(account_move_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": account_move_ids[0],
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", account_move_ids)],
                    "view_mode": "tree,form",
                }
            )
        return action
