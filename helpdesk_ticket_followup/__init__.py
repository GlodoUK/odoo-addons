from . import models
from . import controllers

from odoo import api, SUPERUSER_ID

DEFAULT_SETTINGS = {
    "helpdesk_ticket_followup.glo_is_send_1st_followup": True,
    "helpdesk_ticket_followup.glo_is_send_2nd_followup": True,
    "helpdesk_ticket_followup.glo_is_close_automatically": True,
    "helpdesk_ticket_followup.glo_is_user_followup_mod": True,
    "helpdesk_ticket_followup.glo_1st_followup_hrs": 24,
    "helpdesk_ticket_followup.glo_2nd_followup_hrs": 48,
    "helpdesk_ticket_followup.glo_close_automatically_hrs": 72,
}


def setup_helpdesk_stages(env):
    """Creates helpdesk stages,"""
    team_ids = env["helpdesk.team"].sudo().search([])
    stage_customer_update_id = env.ref(
        "helpdesk_ticket_followup.helpdesk_stage_customer_update"
    )
    mail_1 = env.ref(
        "helpdesk_ticket_followup."
        "helpdesk_ticket_followup_followup_for_ticket_template_1"
    )
    mail_2 = env.ref(
        "helpdesk_ticket_followup."
        "helpdesk_ticket_followup_followup_for_ticket_template_2"
    )
    mail_1_id = mail_1.id if mail_1 else False
    mail_2_id = mail_2.id if mail_2 else False
    if stage_customer_update_id:
        stage_customer_update_id.team_ids = team_ids.ids if team_ids else []
        stage_customer_update_id.glo_followup_mail_temp_1st = mail_1_id
        stage_customer_update_id.glo_followup_mail_temp_2nd = mail_2_id
    else:
        env["helpdesk.stage"].sudo().create(
            {
                "name": "Customer Update",
                "glo_stage_type": "customer_update",
                "sequence": 1,
                "glo_followup_mail_temp_1st": mail_1_id,
                "glo_followup_mail_temp_2nd": mail_2_id,
                "team_ids": [(6, 0, team_ids.ids)] if team_ids else [],
            }
        )
    stage_in_progress_id = env.ref("helpdesk.stage_in_progress")
    if stage_in_progress_id:
        stage_in_progress_id.glo_stage_type = "in_progress"
    stage_solved_id = env.ref("helpdesk.stage_solved")
    if stage_solved_id:
        stage_solved_id.glo_stage_type = "closed"


def _setup_default_settings(cr, registry):
    """Set default settings on module install, adds and sets up stages"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for dict_key, dict_val in DEFAULT_SETTINGS.items():
        parameter_id = env["ir.config_parameter"].search([("key", "=", dict_key)])
        if not parameter_id:
            env["ir.config_parameter"].create(
                {
                    "key": dict_key,
                    "value": dict_val,
                }
            )
    setup_helpdesk_stages(env)
