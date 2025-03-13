from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    can_be_escalated = fields.Boolean(compute="_compute_can_be_escalated")

    @api.model
    def _get_escalated_tag(self):
        tag_id = self.env["helpdesk.tag"].search([("name", "=", "Escalated")], limit=1)

        if not tag_id:
            tag_id = self.env["helpdesk.tag"].create(
                {
                    "name": "Escalated",
                    "color": 9,
                }
            )

        return tag_id

    def _compute_can_be_escalated(self):
        escalated_ticket = self._get_escalated_tag()

        for record in self:
            if escalated_ticket and escalated_ticket in record.tag_ids:
                record.can_be_escalated = False
                continue

            record.can_be_escalated = True

    def _action_escalate(self, msg=None):
        self.ensure_one()

        escalated_tag = self._get_escalated_tag()

        if escalated_tag not in self.tag_ids:
            self.tag_ids = [(4, escalated_tag.id, 0)]
            self.priority = "3"

        if not self.closed_by_partner and msg:
            self.message_post(
                body=msg, message_type="comment", subtype_xmlid="mail.mt_note"
            )
