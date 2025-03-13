from odoo import http
from odoo.http import request
from odoo.tools.safe_eval import safe_eval

from odoo.addons.helpdesk_portal_new_ticket.controllers.portal import (
    NewTicketCustomerPortal,
)


class NewTicketCustomerPortalSubscribers(NewTicketCustomerPortal):
    def return_allowed_partner_subscriber_ids(self):
        """Gets partner, returns all partners from same company,
        so we can subscribe them to same ticket"""
        user_partner_id = request.env.user.partner_id
        return user_partner_id.mapped("parent_id.child_ids").filtered(
            lambda partner: partner != user_partner_id
        )

    def _new_ticket_get_page_view_values(self, **kwargs):
        """Extends get page values, adds partner ids for subscription"""
        res = super()._new_ticket_get_page_view_values(**kwargs)
        res["privacy"] = kwargs.get("privacy", False)
        res[
            "allowed_partner_subscriber_ids"
        ] = self.return_allowed_partner_subscriber_ids()
        return res

    def safe_eval_partner_ids(self, partner_ids):
        """Gets list of strig partner ids, returns partner ids or empty model"""
        safe_partner_ids = set()
        for partner_id in partner_ids:
            partner_id = safe_eval(partner_id)
            if isinstance(partner_id, int):
                safe_partner_ids.add(partner_id)
        return safe_partner_ids

    @http.route()
    def new_helpdesk_ticket_post(self, **kw):
        """Adds subscribers to partner_ids"""
        res = super().new_helpdesk_ticket_post(**kw)
        partner_ids = self.safe_eval_partner_ids(
            request.httprequest.form.getlist("partner_ids[]")
        )
        ticket = res.location.split("/")[-1]
        ticket_id = request.env["helpdesk.ticket"].browse(int(ticket))
        if kw.get("privacy") and kw.get("privacy") == "on":
            ticket_id.sudo().write({"is_private": True})
        else:
            company_partner_ids = self.return_allowed_partner_subscriber_ids()
            follower_partner_ids = (
                ticket_id.mapped("message_follower_ids.partner_id").ids
                if ticket_id.mapped("message_follower_ids.partner_id")
                else []
            )
            for partner_id in partner_ids:
                if (
                    partner_id in company_partner_ids.ids
                    and partner_id not in follower_partner_ids
                ):
                    request.env["mail.followers"].sudo().create(
                        {
                            "res_id": ticket_id.id,
                            "res_model": "helpdesk.ticket",
                            "partner_id": partner_id,
                        }
                    )
        return res
