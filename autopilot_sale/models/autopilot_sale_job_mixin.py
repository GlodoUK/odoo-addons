import logging
import traceback

import psycopg2

from odoo import fields, models
from odoo.exceptions import ConcurrencyError

from odoo.addons.queue_job.exception import RetryableJobError

_logger = logging.getLogger(__name__)

# Left to queue_job, which retries the whole job: a concurrent update or a
# lock is not this record's fault.
_RETRYABLE = (RetryableJobError, ConcurrencyError, psycopg2.OperationalError)


class AutopilotSaleJobMixin(models.AbstractModel):
    """A record whose work runs as a queued job, with its outcome kept on the
    record itself rather than read from ``queue.job`` (which only the Job
    Queue group can read, and which queue_job vacuums).

    ``_queue(method, channel_field)`` queues ``method`` on the record's
    backend channel; the job calls ``_run(work)``, which does nothing unless
    the record is still pending (so Cancel stops a queued job), runs ``work``
    in a savepoint and records ``done``, or ``failed`` with the error.
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
        """Queue the record's job again; each model says which."""
        raise NotImplementedError

    def action_retry(self):
        self.filtered(lambda r: r.state in ("failed", "cancelled"))._requeue()

    def action_cancel(self):
        self.filtered(lambda r: r.state in ("pending", "failed")).state = "cancelled"
