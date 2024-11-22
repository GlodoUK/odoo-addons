from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _routing_create_bounce_email(
        self, email_from, body_html, message, **mail_values
    ):
        # Stop ping-ponging on auto response systems.
        # TODO: Submit this upstream.
        if message.get("X-Auto-Response-Suppress", "") == "All":
            return

        return super()._routing_create_bounce_email(
            email_from, body_html, message, **mail_values
        )
