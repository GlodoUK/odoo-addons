from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    reopen_ticket_stage = fields.Many2one(
        "helpdesk.stage",
        string="Reopen Stage",
        help="The stage to set when a ticket is reopened through the portal",
    )

    allow_portal_ticket_reopen = fields.Boolean(
        string="Allow Ticket Reopening",
        help="Allow customers to reopen tickets through the portal",
        default=True,
    )

    clear_assigned_on_reopen = fields.Boolean(
        string="Clear Assigned on Reopen",
        help="Clear the assigned user when a ticket is reopened through the portal",
        default=False,
    )
