from odoo.addons.helpdesk_portal_new_ticket.controllers.portal import (
    NewTicketCustomerPortal,
)


class NewTicketCustomerPortalSubscribers(NewTicketCustomerPortal):
    def _new_ticket_get_ticket_extra_values(self, **kwargs):
        res = super()._new_ticket_get_ticket_extra_values(**kwargs)
        if kwargs.get("privacy") and kwargs.get("privacy") == "on":
            res.update({"is_private": True})
        return res
