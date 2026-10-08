"""Migration helpers for connectors. Not in ``tools``, which is Odoo-free."""

import logging

from odoo.tools import SQL
from odoo.tools.sql import drop_constraint, table_exists

_logger = logging.getLogger(__name__)


def move_connections(cr, model, references):
    """Moves a connector's own connection ``model`` into
    ``autopilot.connection`` and points ``references``, ``(table, column)``
    pairs, at the moved rows. Returns ``{old id: new id}``.

    Call it from a **pre**-migration, with autopilot updated in the same run:
    the rows must move before the ORM adds the new foreign keys. Shared
    columns are copied as they are, credentials included, and XML ids follow.
    Does nothing if the old table isn't there."""
    table = model.replace(".", "_")
    if not table_exists(cr, table):
        return {}
    if not table_exists(cr, "autopilot_connection"):
        raise RuntimeError(
            f"Moving {model}: autopilot_connection does not exist; update "
            "autopilot in the same run."
        )
    cr.execute(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = %s
           AND column_name <> 'id'
        INTERSECT
        SELECT column_name
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = 'autopilot_connection'
        """,
        [table],
    )
    columns = SQL(", ").join(SQL.identifier(name) for (name,) in cr.fetchall())

    cr.execute(SQL("SELECT id FROM %s ORDER BY id", SQL.identifier(table)))
    mapping = {}
    for (old_id,) in cr.fetchall():
        cr.execute(
            SQL(
                "INSERT INTO autopilot_connection (%s) "
                "SELECT %s FROM %s WHERE id = %s RETURNING id",
                columns,
                columns,
                SQL.identifier(table),
                old_id,
            )
        )
        mapping[old_id] = cr.fetchone()[0]
    if not mapping:
        return mapping

    pairs = SQL(", ").join(SQL("(%s, %s)", old, new) for old, new in mapping.items())
    for ref_table, column in references:
        if not table_exists(cr, ref_table):
            continue
        _drop_foreign_keys(cr, ref_table, column)
        cr.execute(
            SQL(
                "UPDATE %s AS ref SET %s = moved.new "
                "FROM (VALUES %s) AS moved(old, new) WHERE ref.%s = moved.old",
                SQL.identifier(ref_table),
                SQL.identifier(column),
                pairs,
                SQL.identifier(column),
            )
        )
    cr.execute(
        SQL(
            "UPDATE ir_model_data AS imd "
            "SET model = 'autopilot.connection', res_id = moved.new "
            "FROM (VALUES %s) AS moved(old, new) "
            "WHERE imd.model = %s AND imd.res_id = moved.old",
            pairs,
            model,
        )
    )
    _logger.info(
        "autopilot: moved %s %s record(s) into autopilot.connection: %s",
        len(mapping),
        model,
        mapping,
    )
    return mapping


def _drop_foreign_keys(cr, table, column):
    cr.execute(
        """
        SELECT con.conname
          FROM pg_constraint con
          JOIN pg_attribute att
            ON att.attrelid = con.conrelid AND att.attnum = ANY(con.conkey)
         WHERE con.contype = 'f'
           AND con.conrelid = %s::regclass
           AND att.attname = %s
        """,
        [table, column],
    )
    for (name,) in cr.fetchall():
        drop_constraint(cr, table, name)
