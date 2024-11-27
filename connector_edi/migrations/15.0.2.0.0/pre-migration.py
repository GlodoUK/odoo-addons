from odoo.tools.sql import column_exists, table_exists


def migrate(cr, _version):
    if table_exists(cr, "edi_envelope") and column_exists(cr, "edi_envelope", "body"):
        cr.execute(
            """
            ALTER TABLE edi_envelope
            RENAME COLUMN body TO legacy_body;
        """
        )

    if table_exists(cr, "edi_message") and column_exists(cr, "edi_message", "body"):
        cr.execute(
            """
            ALTER TABLE edi_message
            RENAME COLUMN body TO legacy_body;
        """
        )
