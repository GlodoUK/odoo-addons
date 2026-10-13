from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists


def migrate(cr, version):
    """Files now hold several orders, and bindings gained To Send."""
    if column_exists(cr, "autopilot_purchase_order_file", "order_binding_id"):
        cr.execute(
            """
            INSERT INTO autopilot_purchase_order_file_rel (file_id, order_binding_id)
            SELECT id, order_binding_id
              FROM autopilot_purchase_order_file
             WHERE order_binding_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )
    env = api.Environment(cr, SUPERUSER_ID, {})
    bindings = env["autopilot_purchase.order"].search([])
    env.add_to_compute(bindings._fields["state"], bindings)
    bindings.flush_recordset()
