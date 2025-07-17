from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.sale.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):

    @http.route()
    def portal_quote_accept(
        self,
        order_id,
        access_token=None,
        name=None,
        signature=None,
    ):
        res = super().portal_quote_accept(
            order_id=order_id,
            access_token=access_token,
            name=name,
            signature=signature,
        )

        if "error" in res:
            return res

        try:
            order_sudo = self._document_check_access(
                "sale.order",
                order_id,
                access_token=access_token
            )
        except (AccessError, MissingError):
            return {"error": _("Invalid order.")}

        author_id = order_sudo.partner_id.id if request.env.user._is_public() else request.env.user.partner_id.id

        for ticket in order_sudo.helpdesk_tickets_ids:
            ticket.message_post(
                author_id=author_id,
                body=_("Order %s signed by %s") % (order_sudo.name, name),
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

        return res
