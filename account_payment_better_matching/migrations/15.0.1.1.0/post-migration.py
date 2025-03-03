from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        """
    UPDATE
        account_move_line
    SET
        reconcile_override = 0
    WHERE
        reconcile_override is not null
        AND
        reconcile_override != 0
        AND
        reconciled is True
    """
    )
