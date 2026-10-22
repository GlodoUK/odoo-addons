from odoo.addons.helpdesk_portal_new_ticket.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    def _new_ticket_get_page_view_values(self, **kwargs):
        res = super()._new_ticket_get_page_view_values(**kwargs)

        res.update(
            {
                "privacy": kwargs.get("privacy", None),
            }
        )

        return res

    def _new_ticket_get_ticket_extra_values(self, **kwargs):
        res = super()._new_ticket_get_ticket_extra_values(**kwargs)

        if kwargs.get("privacy") and kwargs.get("privacy") == "on":
            res.update({"is_private": True})

        return res
