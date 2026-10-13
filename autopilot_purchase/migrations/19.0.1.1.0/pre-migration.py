from odoo.addons.autopilot.upgrade import move_connections


def migrate(cr, version):
    move_connections(
        cr,
        "autopilot_purchase.connection",
        [("autopilot_purchase_backend", "connection_id")],
    )
