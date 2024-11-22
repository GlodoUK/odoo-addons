import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
MAX_AGE = 90 * 86400


class TwilioSmsLog(models.Model):
    _name = "twilio_sms.log"
    _description = "Twilio SMS Log"
    _order = "create_date desc"

    to = fields.Char()
    body = fields.Text()
    account_sid = fields.Char()
    api_response = fields.Text()
    state = fields.Selection(
        [
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="done",
        required=True,
    )

    @api.autovacuum
    def _gc_log(self):
        self._cr.execute(
            """
            DELETE FROM twilio_sms_log
            WHERE create_date < (NOW() AT TIME ZONE 'UTC' - INTERVAL '%s SECONDS')
            """,
            [MAX_AGE],
        )
        _logger.info("GC'd %d twilio_sms_log entries", self._cr.rowcount)
