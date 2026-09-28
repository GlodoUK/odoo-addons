# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common

from odoo.addons.queue_job.job import Job


class TestQueueJobTrace(common.TransactionCase):
    """The trace is decided entirely in ``queue.job.create``.

    We build real jobs through the :class:`~queue_job.job.Job` class so the
    ``records``/``method_name`` are valid, and drive the opt-in / propagation
    purely through the context - exactly as it happens at runtime, where
    ``with_delay`` threads the recordset context down to ``store``/``create``.
    """

    def _store_job(self, ctx=None):
        model = self.env["res.partner"]
        if ctx:
            model = model.with_context(**ctx)
        job = Job(model.fields_get)
        job.store()
        return job.db_record()

    def test_no_trace_by_default(self):
        record = self._store_job()
        self.assertFalse(record.trace_uuid)
        self.assertFalse(record.parent_uuid)

    def test_opt_in_mints_trace(self):
        record = self._store_job(ctx={"queue_job_trace": True})
        self.assertTrue(record.trace_uuid)
        # no spawner -> it is the root of the trace
        self.assertFalse(record.parent_uuid)

    def test_opt_in_with_correlation_id(self):
        record = self._store_job(ctx={"queue_job_trace": "SO-2026-0042"})
        self.assertEqual(record.trace_uuid, "SO-2026-0042")

    def test_trace_propagates_to_spawned_job(self):
        parent = self._store_job(ctx={"queue_job_trace": "TRACE-1"})
        # a job enqueued while ``parent`` runs carries its uuid in context
        child = self._store_job(ctx={"job_uuid": parent.uuid})
        self.assertEqual(child.trace_uuid, "TRACE-1")
        self.assertEqual(child.parent_uuid, parent.uuid)

    def test_untraced_spawner_does_not_trace_child(self):
        parent = self._store_job()
        child = self._store_job(ctx={"job_uuid": parent.uuid})
        self.assertFalse(child.trace_uuid)

    def test_explicit_start_overrides_inheritance(self):
        parent = self._store_job(ctx={"queue_job_trace": "TRACE-1"})
        child = self._store_job(
            ctx={"job_uuid": parent.uuid, "queue_job_trace": "TRACE-2"}
        )
        self.assertEqual(child.trace_uuid, "TRACE-2")

    def test_current_trace_helper(self):
        parent = self._store_job(ctx={"queue_job_trace": "TRACE-1"})
        trace = (
            self.env["queue.job"].with_context(job_uuid=parent.uuid)._current_trace()
        )
        self.assertEqual(trace, "TRACE-1")
        self.assertFalse(self.env["queue.job"]._current_trace())

    def test_trace_jobs_count_and_graph(self):
        parent = self._store_job(ctx={"queue_job_trace": "TRACE-1"})
        child = self._store_job(ctx={"job_uuid": parent.uuid})
        grandchild = self._store_job(ctx={"job_uuid": child.uuid})

        self.assertEqual(parent.trace_jobs_count, 3)

        graph = parent.trace_graph
        self.assertEqual(len(graph["nodes"]), 3)
        # tree edges: parent -> child -> grandchild
        # ``trace_graph`` is a Serialized field, so edge tuples round-trip
        # through JSON and come back as lists.
        self.assertIn([parent.id, child.id], graph["edges"])
        self.assertIn([child.id, grandchild.id], graph["edges"])
        self.assertEqual(len(graph["edges"]), 2)

    def test_with_trace_helper_tags_job(self):
        job = self.env["res.partner"].with_trace("WD-1").with_delay().fields_get()
        record = self.env["queue.job"].search([("uuid", "=", job.uuid)])
        self.assertEqual(record.trace_uuid, "WD-1")

    def test_with_trace_helper_mints_id(self):
        job = self.env["res.partner"].with_trace().with_delay().fields_get()
        record = self.env["queue.job"].search([("uuid", "=", job.uuid)])
        self.assertTrue(record.trace_uuid)

    def test_cancel_trace(self):
        parent = self._store_job(ctx={"queue_job_trace": "TRACE-1"})
        child = self._store_job(ctx={"job_uuid": parent.uuid})
        parent.cancel_trace()
        self.assertEqual(parent.state, "cancelled")
        self.assertEqual(child.state, "cancelled")
