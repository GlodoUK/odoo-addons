from odoo import http
from odoo.http import request


from odoo.addons.helpdesk_portal_new_ticket.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    def _get_default_ticket_categ_id(self):
        return request.env.ref("helpdesk_ticket_category.type_issue").sudo().id

    def _get_ticket_categ_ids(self):
        domain = self._get_ticket_categ_ids_domain()
        return request.env["helpdesk.ticket.category"].sudo().search(domain)

    def _get_ticket_categ_ids_domain(self):
        return []

    def _new_ticket_get_page_view_values(self, **kwargs):
        res = super()._new_ticket_get_page_view_values(**kwargs)

        res.update(
            {
                "default_categ_id": self._get_default_ticket_categ_id(),
                "ticket_categ_ids": self._get_ticket_categ_ids(),
            }
        )

        return res

    def _new_ticket_get_ticket_extra_values(self, **kwargs):
        res = super()._new_ticket_get_ticket_extra_values(**kwargs)

        res.update(
            {
                "ticket_categ_id": int(kwargs.get("category"))
            }
        )

        return res

    def _get_required_fields(self):
        return super()._get_required_fields() + ["ticket_categ_id"]
