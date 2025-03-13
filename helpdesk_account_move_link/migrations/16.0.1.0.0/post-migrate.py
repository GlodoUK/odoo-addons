from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, _version):
    new = openupgrade.get_legacy_name("helpdesk_ticket_id")

    if openupgrade.column_exists(env.cr, "account_move", "helpdesk_ticket_id"):
        openupgrade.m2o_to_x2m(
            env.cr, env["account.move"], "account_move", "helpdesk_ticket_ids", new
        )

        openupgrade.drop_columns(env.cr, [("account_move", new)])
