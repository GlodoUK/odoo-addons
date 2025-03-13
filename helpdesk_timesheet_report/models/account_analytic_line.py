from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    glo_client_company_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_company", "!=", False)],
        compute="_compute_client_company_id",
        store=True,
    )
    glo_client_company_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_company", "!=", False)],
        compute="_compute_client_company_id",
        store=True,
    )
    glo_ticket_type_id = fields.Many2one(
        comodel_name="helpdesk.ticket.type",
        related="helpdesk_ticket_id.ticket_type_id",
        store=True,
    )
    glo_ticket_category_ids = fields.Many2many(
        comodel_name="helpdesk.ticket.category",
        compute="_compute_glo_ticket_category_ids",
        store=True,
    )

    def _compute_glo_ticket_category_ids(self):
        for obj in self:
            obj.glo_ticket_category_ids = obj.mapped(
                "helpdesk_ticket_id.ticket_category_ids"
            ).ids

    def _compute_client_company_id(self):
        for obj in self:
            ticket_or_task_id = obj.mapped("task_id") or obj.mapped(
                "helpdesk_ticket_id"
            )
            if ticket_or_task_id:
                customer_id = ticket_or_task_id[0].mapped("partner_id")
                if customer_id:
                    customer_id._compute_balance_partner_id()
                    if customer_id.balance_partner_id:
                        obj.glo_client_company_id = customer_id.balance_partner_id.id
