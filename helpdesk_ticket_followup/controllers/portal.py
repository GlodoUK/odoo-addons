import datetime

from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class TicketFollowupCustomerPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        values.update(
            {
                "is_user_followup_mod": request.env["ir.config_parameter"]
                .sudo()
                .get_param(
                    "helpdesk_ticket_followup.glo_is_user_followup_mod", default=False
                ),
            }
        )
        return values

    def return_rewrite_values(self, partner_vals, new_partner_vals):
        """Goes through values, pick ones we want to rewrite for partner"""
        res_dict = {}
        for partner_val_key, _partner_val_val in partner_vals.items():
            if partner_val_key not in new_partner_vals:
                new_partner_vals[partner_val_key] = False
        for partner_val_key, partner_val_val in partner_vals.items():
            if partner_val_key in new_partner_vals:
                if new_partner_vals[partner_val_key] != partner_val_val:
                    res_dict[partner_val_key] = new_partner_vals[partner_val_key]
        return res_dict

    def setup_write_partner_values(self, partner_id, **kw):
        """Picks values from fronent kwargs and send them to return_rewrite_values
        so it decide which values we whatnt to rewrite with one querry"""
        partner_vals = {
            "snooze_till_date": partner_id.snooze_till_date,
            "is_send_followup_1st": partner_id.is_send_followup_1st,
            "is_send_followup_2nd": partner_id.is_send_followup_2nd,
        }
        new_partner_vals = {}
        snooze_till_date = False
        if kw.get("snooze_till_date"):
            snooze_till_date = datetime.datetime.strptime(
                kw.get("snooze_till_date"), "%Y-%m-%d"
            ).date()
        if snooze_till_date and snooze_till_date >= datetime.date.today():
            new_partner_vals["snooze_till_date"] = snooze_till_date
        else:
            new_partner_vals["snooze_till_date"] = False
        if kw.get("followup_1st"):
            new_partner_vals["is_send_followup_1st"] = True
        if kw.get("followup_2nd"):
            new_partner_vals["is_send_followup_2nd"] = True
        return self.return_rewrite_values(partner_vals, new_partner_vals)

    @http.route(
        ["/my/followup_settings"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
        methods=["GET", "POST"],
    )
    def ticket_followup_settings(self, **kw):
        """Shows user's followup settings, writes them to model if changes"""
        if request.httprequest.method == "GET":
            cur_partner_id = request.env.user.partner_id
            snooze_till_date = ""
            if (
                cur_partner_id.snooze_till_date
                and cur_partner_id.snooze_till_date >= datetime.date.today()
            ):
                snooze_till_date = cur_partner_id.snooze_till_date
            params = request.env["ir.config_parameter"].sudo()
            values = {
                "page_name": "Followup settings",
                "cur_partner_id": cur_partner_id,
                "snooze_till_date": snooze_till_date,
                "glo_1st_followup_hrs": int(
                    params.get_param(
                        "helpdesk_ticket_followup.glo_1st_followup_hrs", default=0
                    )
                ),
                "glo_2nd_followup_hrs": int(
                    params.get_param(
                        "helpdesk_ticket_followup.glo_2nd_followup_hrs", default=0
                    )
                ),
                "glo_close_automatically_hrs": int(
                    params.get_param(
                        "helpdesk_ticket_followup.glo_close_automatically_hrs",
                        default=0,
                    )
                ),
            }
            return request.render(
                "helpdesk_ticket_followup."
                "helpdesk_ticket_followup_ticket_followup_settings_page",
                values,
            )

        if request.httprequest.method == "POST":
            partner_id = request.env.user.partner_id
            partner_id.write(self.setup_write_partner_values(partner_id, **kw))
        return request.redirect("/my/tickets")
