import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.table_exists(env.cr, "account_invoice"):
        _logger.warning(
            "Skipped brands migration because account_invoice" " table does not exist"
        )
        return

    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET
            brand_id = ai.brand_id
        FROM account_invoice ai
        WHERE ai.move_id = am.id
        """,
    )
