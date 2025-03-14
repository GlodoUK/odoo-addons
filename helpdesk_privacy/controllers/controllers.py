from operator import itemgetter

from odoo import _, http
from odoo.http import request
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager

from .new_ticket_customer_portal import (
    NewTicketCustomerPortalSubscribers,
)


class CustomerPortalHelpdeskPrivacy(CustomerPortal):
    def _prepare_helpdesk_tickets_domain(self):
        tickets_domain = super()._prepare_helpdesk_tickets_domain()
        following_tickets_ids = (
            request.env["mail.followers"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "helpdesk.ticket"),
                    ("partner_id", "=", request.env.user.partner_id.id),
                ]
            )
            .mapped("res_id")
        )
        add_tickets_domain = [
            "|",
            ("partner_id", "=", request.env.user.partner_id.id),
            ("id", "in", following_tickets_ids),
        ]
        for item in add_tickets_domain:
            tickets_domain.append(item)
        return tickets_domain

    @http.route(
        ["/my/tickets", "/my/tickets/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    # pylint: disable=R0914,R0912,R0915
    # flake8: noqa: C901
    def my_helpdesk_tickets(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby="all",
        search=None,
        groupby="none",
        search_in="content",
        **kw,
    ):
        values = self._prepare_portal_layout_values()

        searchbar_sortings = {
            "date": {"label": _("Newest"), "order": "create_date desc"},
            "name": {"label": _("Subject"), "order": "name"},
            "stage": {"label": _("Stage"), "order": "stage_id"},
            "reference": {"label": _("Reference"), "order": "id"},
            "update": {
                "label": _("Last Stage Update"),
                "order": "date_last_stage_update desc",
            },
        }
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
            "assigned": {"label": _("Assigned"), "domain": [("user_id", "!=", False)]},
            "unassigned": {
                "label": _("Unassigned"),
                "domain": [("user_id", "=", False)],
            },
            "open": {"label": _("Open"), "domain": [("close_date", "=", False)]},
            "closed": {"label": _("Closed"), "domain": [("close_date", "!=", False)]},
            "last_message_sup": {"label": _("Last message is from support")},
            "last_message_cust": {"label": _("Last message is from customer")},
        }
        searchbar_inputs = {
            "content": {
                "input": "content",
                "label": _("Search  in Content"),
            },
            "message": {"input": "message", "label": _("Search in Messages")},
            "customer": {"input": "customer", "label": _("Search in Customer")},
            "id": {"input": "id", "label": _("Search in Reference")},
            "status": {"input": "status", "label": _("Search in Stage")},
            "all": {"input": "all", "label": _("Search in All")},
        }
        searchbar_groupby = {
            "none": {"input": "none", "label": _("None")},
            "stage": {"input": "stage_id", "label": _("Stage")},
        }

        # default sort by value
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        if filterby in ["last_message_sup", "last_message_cust"]:
            discussion_subtype_id = request.env.ref("mail.mt_comment").id
            messages = request.env["mail.message"].search_read(
                [
                    ("model", "=", "helpdesk.ticket"),
                    ("subtype_id", "=", discussion_subtype_id),
                ],
                fields=["res_id", "author_id"],
                order="date desc",
            )
            last_author_dict = {}
            for message in messages:
                if message["res_id"] not in last_author_dict:
                    last_author_dict[message["res_id"]] = message["author_id"][0]

            ticket_author_list = request.env["helpdesk.ticket"].search_read(
                fields=["id", "partner_id"]
            )
            ticket_author_dict = {
                ticket_author["id"]: ticket_author["partner_id"][0]
                if ticket_author["partner_id"]
                else False
                for ticket_author in ticket_author_list
            }

            last_message_cust = []
            last_message_sup = []
            for ticket_id in (
                last_author_dict.keys()  # noqa: C0201
            ):  # noqa: C0201
                if last_author_dict[ticket_id] == ticket_author_dict[ticket_id]:
                    last_message_cust.append(ticket_id)
                else:
                    last_message_sup.append(ticket_id)

            if filterby == "last_message_cust":
                domain = [("id", "in", last_message_cust)]
            else:
                domain = [("id", "in", last_message_sup)]

        else:
            domain = searchbar_filters[filterby]["domain"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ("id", "all"):
                search_domain = OR([search_domain, [("id", "ilike", search)]])
            if search_in in ("content", "all"):
                search_domain = OR(
                    [
                        search_domain,
                        [
                            "|",
                            ("name", "ilike", search),
                            ("description", "ilike", search),
                        ],
                    ]
                )
            if search_in in ("customer", "all"):
                search_domain = OR([search_domain, [("partner_id", "ilike", search)]])
            if search_in in ("message", "all"):
                discussion_subtype_id = request.env.ref("mail.mt_comment").id
                search_domain = OR(
                    [
                        search_domain,
                        [
                            ("message_ids.body", "ilike", search),
                            ("message_ids.subtype_id", "=", discussion_subtype_id),
                        ],
                    ]
                )
            if search_in in ("status", "all"):
                search_domain = OR([search_domain, [("stage_id", "ilike", search)]])
            domain += search_domain

        # Domain privacy
        current_users_domain = self._prepare_helpdesk_tickets_domain()
        for domain_item in current_users_domain:
            domain.append(domain_item)
        # pager
        tickets_count = len(request.env["helpdesk.ticket"].sudo().search(domain))
        pager = portal_pager(
            url="/my/tickets",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "search_in": search_in,
                "search": search,
                "groupby": groupby,
            },
            total=tickets_count,
            page=page,
            step=self._items_per_page,
        )

        tickets = (
            request.env["helpdesk.ticket"]
            .sudo()
            .search(
                domain, order=order, limit=self._items_per_page, offset=pager["offset"]
            )
        )
        request.session["my_tickets_history"] = tickets.ids[:100]

        if groupby == "stage":
            grouped_tickets = [
                request.env["helpdesk.ticket"].concat(*g)
                for k, g in groupbyelem(tickets, itemgetter("stage_id"))
            ]
        else:
            grouped_tickets = [tickets]

        values.update(
            {
                "date": date_begin,
                "grouped_tickets": grouped_tickets,
                "page_name": "ticket",
                "default_url": "/my/tickets",
                "pager": pager,
                "searchbar_sortings": searchbar_sortings,
                "searchbar_filters": searchbar_filters,
                "searchbar_inputs": searchbar_inputs,
                "searchbar_groupby": searchbar_groupby,
                "sortby": sortby,
                "groupby": groupby,
                "search_in": search_in,
                "search": search,
                "filterby": filterby,
            }
        )
        return request.render("helpdesk.portal_helpdesk_ticket", values)

    @http.route(
        [
            "/helpdesk/ticket/<int:ticket_id>",
            "/helpdesk/ticket/<int:ticket_id>/<access_token>",
            "/my/ticket/<int:ticket_id>",
            "/my/ticket/<int:ticket_id>/<access_token>",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def tickets_followup(self, ticket_id=None, access_token=None, **kw):
        res = super().tickets_followup(ticket_id, access_token, **kw)
        if res == request.redirect("/my"):
            return res
        ticket = request.env["helpdesk.ticket"].sudo().browse(ticket_id)
        if ticket.is_private:
            user = request.env["res.users"].browse(request.uid)
            partner = user.partner_id
            if (
                partner not in ticket.message_partner_ids
                and not partner == ticket.partner_id
                and not user == ticket.create_uid
            ):
                return request.redirect("/my")
        res.qcontext["allowed_portal_partner_ids"] = ticket.allowed_portal_partner_ids
        res.qcontext[
            "active_portal_follower_ids"
        ] = ticket.message_partner_ids.filtered(
            lambda fol_id: fol_id in ticket.allowed_portal_partner_ids
        )
        res.qcontext["ticket_id"] = ticket.id
        res.qcontext["is_private"] = ticket.is_private
        return res

    @http.route(
        [
            "/my/ticket/update_follower_ids/<int:inc_ticket_id>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def update_follower_ids(self, inc_ticket_id, **kw):
        """Updates follower ids for customer, his siblings,
        customer technician, assignee, helpdesk team staff"""
        if request.httprequest.method == "POST":
            ticket_id = request.env["helpdesk.ticket"].browse(int(inc_ticket_id))
            customer_siblings_ids = ticket_id.sudo().mapped(
                "partner_id.parent_id.child_ids"
            )
            authorized_update_partner_ids = (
                ticket_id.sudo().mapped("partner_id")
                | customer_siblings_ids
                | ticket_id.sudo().mapped("user_id.partner_id")
                | ticket_id.sudo().mapped("technical_user_id.partner_id")
                | ticket_id.sudo().mapped(
                    "team_id.glo_helpdesk_support_ids.support_user_id.partner_id"
                )
            )
            curr_partner_id = request.env.user.partner_id
            if ticket_id and curr_partner_id in authorized_update_partner_ids:
                updated_follower_ids = (
                    NewTicketCustomerPortalSubscribers.safe_eval_partner_ids(
                        self, request.httprequest.form.getlist("follower_ids[]")
                    )
                )
                message_followers_ids = ticket_id.sudo().mapped("message_follower_ids")
                remove_message_followers_ids = message_followers_ids.filtered(
                    lambda follower_id: follower_id.partner_id in customer_siblings_ids
                    and follower_id.partner_id.id not in updated_follower_ids
                )
                remove_message_followers_ids.sudo().unlink()
                message_followers_ids -= remove_message_followers_ids
                for updated_follower_id in updated_follower_ids:
                    if (
                        updated_follower_id
                        not in message_followers_ids.mapped("partner_id").ids
                    ):
                        request.env["mail.followers"].sudo().create(
                            {
                                "res_id": inc_ticket_id,
                                "res_model": "helpdesk.ticket",
                                "partner_id": updated_follower_id,
                            }
                        )
            return request.redirect(f"/helpdesk/ticket/{inc_ticket_id}")
        return False
