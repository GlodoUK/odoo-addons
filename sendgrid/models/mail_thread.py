import ast
import logging
from odoo import models, tools

AUTO_RESPOND_HEADERS = {
    # header: [valuestoignore]
    'X-Auto-Response-Suppress': None,
    'X-Autoreply': None,
    'X-Autorespond': None,
    'Auto-Submitted': ['no']
}

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _is_auto_response_email_message(self, message):
        # Check if any auto respond headers are present in the original email.
        # If they are, then we need to suppress the bounce.
        for key, values_to_ignore in AUTO_RESPOND_HEADERS.items():
            if key not in message:
                continue

            # Header was present, we need to check the value to see if it matches
            # a value we can skip
            if values_to_ignore and message.get(key) in values_to_ignore:
                continue

            # Header was present, but we don't need to check the value
            return True

    def _routing_create_bounce_email(
        self, email_from, body_html, message, **mail_values
    ):
        # Drop any auto responses without sending a bounce at risk of infinite
        # loops

        # Find where we're sending the bounce to
        bounce_to = (
            tools.decode_message_header(message, 'Return-Path') or email_from
        )

        if self._is_auto_response_email_message(message):
            _logger.info(
                "Dropping bounce response to %s due to detected auto-response"
                " header" % (bounce_to)
            )
            return

        # Use the built in blacklist
        blacklisted = self.env['mail.blacklist'].search_count([
            ('email', '=', bounce_to)
        ])

        if blacklisted > 0:
            _logger.info(
                "Dropping bounce response to %s due to being on mail.blacklist"
                % (
                    bounce_to
                )
            )
            return

        # We need to add some indicators to suggest this bounce shouldn't get a
        # response from dumb auto responders
        extra_headers = {
            "X-Auto-Response-Suppress": "All",
            "Auto-submitted": "auto-replied",
        }

        # If we've got a string headers immediately convert it to a real dict,
        # if we can
        if (
            mail_values.get('headers')
            and
            isinstance(mail_values.get('headers'), str)
        ):
            try:
                original_headers = ast.literal_eval(mail_values['headers'])
                mail_values.update(original_headers)
            except Exception:
                # This is safe to drop because thats what upstream does if the
                # decoding fails
                del mail_values['headers']

        # Now add our extra headers
        if isinstance(mail_values.get('headers'), dict):
            mail_values['headers'].update(extra_headers)
        else:
            mail_values['headers'] = extra_headers

        return super()._routing_create_bounce_email(
            email_from,
            body_html,
            message,
            **mail_values
        )
