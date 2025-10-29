from odoo.addons.helpdesk.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    def _ticket_get_page_view_values(self, ticket, access_token, **kwargs):
        res = super()._ticket_get_page_view_values(ticket, access_token, **kwargs)
        res["ticket_type_properties"] = ticket._display_ticket_type_properties()
        return res
