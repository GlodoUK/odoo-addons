import logging
import traceback

import psycopg2

from odoo import api, fields, models
from odoo.exceptions import ConcurrencyError

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

# Left to queue_job to retry: a lock or concurrent update is not this
# record's fault.
_RETRYABLE = (RetryableJobError, ConcurrencyError, psycopg2.OperationalError)


class AutopilotSaleJobMixin(models.AbstractModel):
    """A record whose work runs as a queued job, keeping its own outcome.

    ``queue.job`` is no place for it: only the Job Queue group can read it,
    and queue_job vacuums it. ``_run`` does nothing unless the record is still
    pending, so Cancel stops a queued job.
    """

    _name = "autopilot_sale.job.mixin"
    _description = "Sale EDI Queued Work"

    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("done", "Done"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
        required=True,
        readonly=True,
        copy=False,
        index=True,
    )
    error = fields.Char(readonly=True, copy=False)
    error_detail = fields.Text(readonly=True, copy=False)

    def _queue(self, method, channel_field):
        for record in self:
            record.write({"state": "pending", "error": False, "error_detail": False})
            backend = record.backend_id
            getattr(backend._delay(record, backend[channel_field]), method)()

    def _run(self, work):
        self.ensure_one()
        if self.state != "pending":
            return
        try:
            with self.env.cr.savepoint():
                work()
        except _RETRYABLE:
            raise
        except Exception as exc:
            _logger.exception("Sale EDI: %s failed.", self.display_name)
            self.write(
                {
                    "state": "failed",
                    "error": str(exc) or type(exc).__name__,
                    "error_detail": traceback.format_exc(),
                }
            )
            return
        self.write({"state": "done", "error": False, "error_detail": False})

    def _requeue(self):
        raise NotImplementedError

    def action_retry(self):
        self.filtered(lambda r: r.state in ("failed", "cancelled"))._requeue()

    def action_cancel(self):
        self.filtered(lambda r: r.state in ("pending", "failed")).state = "cancelled"

    @api.model
    def _autopilot_activity_query(self):
        return self.env["autopilot.activity"]._source_select(
            self,
            backend="backend_id",
            company="company_id",
            state="state",
            status={
                "pending": "pending",
                "done": "done",
                "failed": "error",
                "cancelled": "cancelled",
            },
            error="error",
        )

    def _autopilot_activity_retry(self):
        return self.action_retry()

    def _autopilot_activity_cancel(self):
        return self.action_cancel()
