from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Remove broken view
    view = env.ref(
        "helpdesk_privacy.helpdesk_privacy_tickets_followup", raise_if_not_found=False
    )

    if view:
        view.active = False
