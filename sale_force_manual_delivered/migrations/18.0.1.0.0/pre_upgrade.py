from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    views_to_uninstall = [
        "sale_force_manual_delivered.glodo_sale_view_order_form",
    ]

    for view in views_to_uninstall:
        if env.ref(view, raise_if_not_found=False):
            view.unlink()
