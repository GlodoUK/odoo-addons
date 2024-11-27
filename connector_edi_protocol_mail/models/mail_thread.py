from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def _message_route_process(self, message, message_dict, routes):
        # insert the raw message into custom_values for our usage in
        # edi.envelope.route
        is_envelope_route = False
        for r in routes:
            if r[0] == "edi.envelope.route":
                r[2]["message"] = message
                is_envelope_route = True

        res = super()._message_route_process(message, message_dict, routes)

        if res and is_envelope_route:
            envelope_ids = self.env["edi.envelope"].browse(res)
            envelope_ids.action_pending()

        return res
