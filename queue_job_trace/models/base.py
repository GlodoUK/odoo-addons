from odoo import models

from .queue_job import TRACE_CONTEXT_KEY


class Base(models.AbstractModel):
    _inherit = "base"

    def with_trace(self, trace=True):
        """Start (or join) a trace for jobs enqueued from this recordset.

        Returns a recordset whose ``with_delay`` / ``delayable`` calls will
        tag the resulting job with a trace id, and jobs spawned while that job
        runs inherit the trace automatically.

        ``trace=True`` mints a fresh trace id, ``trace="SO-2026-0042"`` uses
        your own correlation id (handy to correlate the flow with external
        logs). Usage::

            self.with_trace("SO-2026-0042").with_delay().step_one(...)
            self.env["x"].with_trace().delayable().step_one(...).delay()

        It is a shortcut for
        ``self.with_context(queue_job_trace=trace)``.
        """
        return self.with_context(**{TRACE_CONTEXT_KEY: trace})
