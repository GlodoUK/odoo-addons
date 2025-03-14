from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, _version):
    if openupgrade.column_exists(env.cr, "account_move", "helpdesk_ticket_id"):
        openupgrade.rename_columns(
            env.cr, {"account_move": [("helpdesk_ticket_id", None)]}
        )
