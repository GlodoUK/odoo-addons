from odoo.addons.autopilot.upgrade import move_connections


def migrate(cr, version):
    move_connections(
        cr,
        "autopilot_sale.connection",
        [("autopilot_sale_backend", "connection_id")],
    )
