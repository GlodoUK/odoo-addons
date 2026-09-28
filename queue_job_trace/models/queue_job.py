import logging
import uuid

from odoo import api, fields, models

from odoo.addons.base_sparse_field.models.fields import Serialized

_logger = logging.getLogger(__name__)

# Context key used to opt in to tracing. Prefer the ``with_trace()`` helper
# (see ``models/base.py``) over setting this directly. Set it to ``True`` to
# mint a fresh trace id, or to a string to use your own correlation id (e.g.
# an external request id, a document name...). Jobs spawned during a traced
# job inherit the trace automatically.
TRACE_CONTEXT_KEY = "queue_job_trace"


class QueueJob(models.Model):
    _inherit = "queue.job"

    trace_uuid = fields.Char(
        string="Trace",
        index=True,
        readonly=True,
        help="Shared identifier correlating every job spawned, directly or "
        "transitively, from the same traced origin. Empty unless tracing "
        "was explicitly requested.",
    )
    parent_uuid = fields.Char(
        string="Spawned By",
        index=True,
        readonly=True,
        help="UUID of the job during whose execution this job was enqueued. "
        "Used to reconstruct the trace tree.",
    )
    trace_graph = Serialized(compute="_compute_trace_graph")
    trace_jobs_count = fields.Integer(compute="_compute_trace_jobs_count")

    @api.model_create_multi
    @api.private
    def create(self, vals_list):
        spawner_uuid = self.env.context.get("job_uuid")
        requested = self.env.context.get(TRACE_CONTEXT_KEY)
        spawner_trace = None
        if spawner_uuid and not requested:
            spawner = self.search([("uuid", "=", spawner_uuid)], limit=1)
            spawner_trace = spawner.trace_uuid or None

        for vals in vals_list:
            if vals.get("trace_uuid"):
                # explicitly set by the caller, leave it untouched
                trace = vals["trace_uuid"]
            elif isinstance(requested, str) and requested:
                # opt in with a caller-supplied correlation id
                trace = requested
            elif requested:
                # opt in, mint a fresh trace id
                trace = str(uuid.uuid4())
            elif spawner_trace:
                # propagate an ongoing trace to the spawned job
                trace = spawner_trace
            else:
                trace = False

            if trace:
                vals["trace_uuid"] = trace
                if spawner_uuid:
                    vals["parent_uuid"] = spawner_uuid

        records = super().create(vals_list)

        for record in records.filtered("trace_uuid"):
            _logger.info(
                "queue.job %s enqueued in trace %s (parent %s)",
                record.uuid,
                record.trace_uuid,
                record.parent_uuid or "-",
            )
        return records

    @api.model
    def _current_trace(self):
        """Return the trace id of the job currently being executed, if any.

        Can be called from within a job's method to log or forward the trace
        id, e.g. ``self.env["queue.job"]._current_trace()``.
        """
        job_uuid = self.env.context.get("job_uuid")
        if not job_uuid:
            return False
        job = self.search([("uuid", "=", job_uuid)], limit=1)
        return job.trace_uuid or False

    def _trace_siblings(self):
        """Return every job sharing this record's trace."""
        traces = [t for t in self.mapped("trace_uuid") if t]
        if not traces:
            return self.browse()
        return self.search([("trace_uuid", "in", traces)])

    def _compute_trace_jobs_count(self):
        traces = [t for t in self.mapped("trace_uuid") if t]
        if traces:
            count_per_trace = dict(
                self.env["queue.job"]._read_group(
                    [("trace_uuid", "in", traces)],
                    groupby=["trace_uuid"],
                    aggregates=["__count"],
                )
            )
        else:
            count_per_trace = {}
        for record in self:
            record.trace_jobs_count = count_per_trace.get(record.trace_uuid) or 0

    def _compute_trace_graph(self):
        traces = [t for t in self.mapped("trace_uuid") if t]
        if traces:
            ids_per_trace = dict(
                self.env["queue.job"]._read_group(
                    [("trace_uuid", "in", traces)],
                    groupby=["trace_uuid"],
                    aggregates=["id:array_agg"],
                )
            )
        else:
            ids_per_trace = {}
        for record in self:
            if not record.trace_uuid:
                record.trace_graph = {}
                continue

            jobs = self.browse(ids_per_trace.get(record.trace_uuid) or [])
            if not jobs:
                record.trace_graph = {}
                continue

            ids_by_uuid = {job.uuid: job.id for job in jobs}
            edges = []
            for job in jobs:
                parent_id = ids_by_uuid.get(job.parent_uuid)
                if parent_id:
                    # (from parent, to child), same convention as the
                    # dependency graph widget
                    edges.append((parent_id, job.id))

            record.trace_graph = {
                "nodes": [job._dependency_graph_vis_node() for job in jobs],
                "edges": edges,
            }

    def open_trace_jobs(self):
        self.ensure_one()
        return {
            "name": self.env._("Trace Jobs"),
            "type": "ir.actions.act_window",
            "res_model": "queue.job",
            "view_mode": "list,form",
            "domain": [("trace_uuid", "=", self.trace_uuid)],
        }

    def cancel_trace(self):
        """Cancel every not-yet-finished job sharing this record's trace."""
        cancellable = self._trace_siblings().filtered(
            lambda j: j.state in ("wait_dependencies", "pending", "enqueued")
        )
        cancellable._change_job_state("cancelled")
        return True
