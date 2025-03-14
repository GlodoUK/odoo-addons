import json
import logging

import requests

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ACTION_COLOR_DICT = {
    "posted a message in the": "Accent",
    "opened": "Attention",
    "closed": "Good",
    "reopened": "Warning",
}
ACTION_NAME_DICT = {
    "posted a message in the": "Message",
    "opened": "Opened",
    "closed": "Closed",
    "reopened": "Reopened",
}
TIMEOUT = 20


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    # http.request.env['ir.config_parameter'].sudo().get_param(
    #     'gocardless.gc_access_token')

    # Hamsa Abdi (Glo) updated ticket GH101627 - New User Setups (Coombe Castle)

    def get_webhook_url(self):
        """Returns teams webhook url from settings"""
        webhook_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("helpdesk_teams_message.glo_teams_webhook_url")
        )
        if webhook_url:
            return webhook_url
        raise UserError(_("Please, set Microsoft Teams Webhook in settings."))

    def prepare_teams_json_data(self, res_message, message_action):
        """Puts message into standard teams AdaptiveCard"""
        is_header_subtle = not ACTION_NAME_DICT.get(message_action) == "Message"
        json_data = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "speak": "<s>f'Ticket {ACTION_NAME_DICT.get(message_action)}'</s>",  # noqa: E501
                        "type": "AdaptiveCard",
                        "version": "1.2",
                        "msTeams": {"width": "full"},
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": f"Ticket {ACTION_NAME_DICT.get(message_action)}",  # noqa: E501
                                "weight": "Bolder",
                                "spacing": "None",
                                "fontType": "Default",
                                "size": "Large",
                                "color": ACTION_COLOR_DICT.get(message_action),
                                "horizontalAlignment": "Center",
                                "wrap": True,
                                "isSubtle": is_header_subtle,
                                "style": "heading",
                            },
                            {
                                "type": "TextBlock",
                                "text": res_message,
                                "weight": "Default",
                                "color": "Dark",
                                "separator": True,
                                "wrap": True,
                                "horizontalAlignment": "Left",
                                "style": "default",
                                "size": "Default",
                            },
                        ],
                        "verticalContentAlignment": "Center",
                    },
                }
            ],
        }
        return json_data

    def return_message_action(self, method_name):
        self.ensure_one()
        if method_name == "message":
            return "posted a message in the"
        if method_name == "create":
            return "opened"
        if method_name == "write":
            if self.team_id:
                if self.stage_id in self.team_id._get_closing_stage():
                    return "closed"
                if self.stage_id == self.team_id._determine_stage().get(1):
                    return "reopened"
        return False

    def return_ticket_names(self, closed_by_partner, author_id):
        """Returns parameters:
        - partner_name - partner's name who changed ticket
        - company_name - company name of a partner who changed ticket
        - client_name - client name inside ticket
        Incoming parameters:
        closed_by_partner: Boolean
        author_id env['res.partner']
        """
        self.ensure_one()
        if not author_id:
            author_id = self.write_uid.partner_id
        company_name = f" ({author_id.parent_id.name})" if author_id.parent_id else ""
        client_name = f" ({self.partner_id.display_name})" if self.partner_id else ""
        partner_name = author_id.display_name
        if closed_by_partner:
            # closed by any user from portal
            partner_name = "Client"
        elif self.stage_id == self.team_id._determine_stage().get(
            1
        ) and author_id == self.env.ref("base.partner_root"):
            # reopened ticket (as odoobot) i.e. from portal
            partner_name = "Client"
        return partner_name, company_name, client_name

    def generate_ticket_url(self):
        self.ensure_one()
        ticket_url = (
            f"{self.env['ir.config_parameter'].get_param('web.base.url')}"
            f"/web#id={self.id}&active_id={self.id}&menu_id="
            f"{self.env.ref('helpdesk.menu_helpdesk_root').id}"
            f"&action={self.env.ref('helpdesk.helpdesk_ticket_action_team').id}"
            f"&model=helpdesk.ticket&view_type=form"
        )
        return ticket_url

    def send_webhook_data(self, method_name, closed_by_partner=False, author_id=False):
        """Sends webhook data if data fits message action"""
        webhook_url = self.get_webhook_url()
        for obj in self:
            message_action = obj.return_message_action(method_name)
            if message_action:
                partner_name, company_name, client_name = obj.return_ticket_names(
                    closed_by_partner, author_id
                )
                ticket_url = obj.generate_ticket_url()
                res_message = (
                    f"{partner_name}{company_name} **{message_action}** "
                    f"ticket [{obj.display_name}{client_name}]({ticket_url})"
                )
                json_data = self.prepare_teams_json_data(res_message, message_action)
                res = requests.post(
                    webhook_url, data=json.dumps(json_data), timeout=TIMEOUT
                )
                if res.status_code != 200:
                    _logger.info(_("Failed to send message to Teams: %s"), res_message)

    @api.model
    def create(self, vals):
        """Sends webhook to teams"""
        res = super().create(vals)
        res.send_webhook_data("create")
        return res

    def write(self, vals):
        """Sends webhook to teams if needed"""
        res = super().write(vals)
        for obj in self:
            if "stage_id" in vals:
                obj.send_webhook_data("write", vals.get("closed_by_partner"))
        return res
