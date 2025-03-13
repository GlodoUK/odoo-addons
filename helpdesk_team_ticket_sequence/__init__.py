from odoo import api, SUPERUSER_ID
from . import models


def _post_init_setup_sequence(cr, registry):
    """Sets up teams_ticket_number_seq as default ticket sequence for every team"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    helpdesk_team_ids = env["helpdesk.team"].sudo().search([])
    if helpdesk_team_ids:
        helpdesk_team_ids.sudo().write(
            {
                "ticket_sequence_id": env.ref(
                    "helpdesk_team_ticket_sequence.teams_ticket_number_seq"
                )
            }
        )
