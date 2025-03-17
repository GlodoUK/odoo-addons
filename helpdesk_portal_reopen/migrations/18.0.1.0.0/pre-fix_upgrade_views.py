from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Remove broken view
    view = env.ref(
        "helpdesk_portal_reopen.helpdesk_portal_reopen_tickets_followup_reopen_ticket",
        raise_if_not_found=False,
    )

    if view:
        view.active = False
