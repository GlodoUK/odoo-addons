from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def _message_route_process(self, message, message_dict, routes):
        # insert the raw message into custom_values for our usage in
        # edi.envelope.route
        for r in routes:
            if r[0] == "edi.envelope.route":
                r[2]["message"] = message

        return super(MailThread, self)._message_route_process(
            message, message_dict, routes
        )
