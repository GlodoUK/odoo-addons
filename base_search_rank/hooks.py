import logging

import psycopg2

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    env.cr.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
    if env.cr.fetchone():
        return
    try:
        env.cr.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    except psycopg2.Error as e:
        raise UserError(
            env._(
                "base_search_rank requires the pg_trgm extension. Automatic "
                "installation failed (usually a permissions issue); run "
                '"CREATE EXTENSION pg_trgm;" as a database superuser and retry.'
            )
        ) from e
    # has_trigram was snapshotted at registry init, before the extension
    # existed; correct it so consumer modules installed in this same registry
    # load still get their GIN indexes built by check_indexes().
    env.registry.has_trigram = True
    _logger.info("Created the pg_trgm extension")
