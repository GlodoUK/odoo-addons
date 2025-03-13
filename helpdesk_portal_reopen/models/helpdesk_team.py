from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    allow_portal_ticket_reopen = fields.Boolean(
        string="Allow Ticket Reopening",
        default=True,
        help="Allow customers to reopen tickets through the portal",
    )

    clear_assigned_on_reopen = fields.Boolean(
        help="Clear the assigned user when a ticket is reopened through the portal",
    )

    reopen_ticket_stage = fields.Many2one(
        "helpdesk.stage",
        string="Reopen Stage",
        help="The stage to set when a ticket is reopened through the portal",
    )
