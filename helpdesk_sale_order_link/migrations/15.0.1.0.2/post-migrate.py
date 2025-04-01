from odoo import SUPERUSER_ID, api


def _move_helpdesk_tickets_m2o_to_m2m(env):
    for so_id in env["sale.order"].sudo().search([]):
        if (
            "helpdesk_ticket_id" in env["product.product"]._fields
            and so_id.helpdesk_ticket_id
        ):
            so_id.write(
                {
                    "helpdesk_tickets_ids": [(6, 0, [so_id.helpdesk_ticket_id.id])],
                    "helpdesk_ticket_id": False,
                }
            )


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _move_helpdesk_tickets_m2o_to_m2m(env)
