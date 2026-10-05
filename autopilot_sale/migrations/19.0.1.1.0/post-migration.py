import logging

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Post, while the old columns are still there (Odoo drops a removed
    field's column only once every module is loaded)."""
    _migrate_states(cr)
    _migrate_connections(cr)


def _migrate_states(cr):
    """Files kept their outcome on their queue job; it is now their own
    state. A file whose job is gone counts as done. Existing order bindings
    all have their sale order, so are done."""
    if column_exists(cr, "autopilot_sale_order_file", "job_state"):
        cr.execute(
            """
            UPDATE autopilot_sale_order_file
               SET state = CASE
                       WHEN job_state IS NULL OR job_state = 'done' THEN 'done'
                       WHEN job_state IN ('failed', 'cancelled') THEN job_state
                       ELSE 'pending'
                   END,
                   error = job_exc_message,
                   error_detail = job_exc_info
            """
        )
        _logger.info("autopilot_sale: %s file state(s) migrated", cr.rowcount)
    cr.execute(
        "UPDATE autopilot_sale_order SET state = 'done' WHERE odoo_id IS NOT NULL"
    )


def _migrate_connections(cr):
    """provider + storage_options on each backend -> a shared
    autopilot_sale.connection."""
    if not column_exists(cr, "autopilot_sale_backend", "provider"):
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(
        """
        SELECT id, provider, storage_options, company_id
          FROM autopilot_sale_backend
         WHERE provider IS NOT NULL AND provider != 'disabled'
         ORDER BY id
        """
    )
    Connection = env["autopilot_sale.connection"]
    Backend = env["autopilot_sale.backend"].with_context(active_test=False)
    for backend_id, protocol, options, company_id in cr.fetchall():
        connection = Connection._from_legacy(protocol, options, company_id or False)
        Backend.browse(backend_id).connection_id = connection
        _logger.info(
            "autopilot_sale: backend %s -> connection %s", backend_id, connection.name
        )
