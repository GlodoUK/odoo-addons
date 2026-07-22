Pipeline
========

Pipeline turns ordinary Odoo methods into background pipelines. You write plain
methods, mark the ones that should run in the background, and Pipeline runs them as
jobs - fanning one out into many and keeping the whole run observable and easy
to retry. The background engine is pluggable: install ``pipeline_queue_job`` to run
on OCA ``queue_job``.

That is all it does. There are no connectors, mappers, schedules or stored
workflow definitions to learn - a concrete addon wires those up with normal
Odoo models and triggers.

.. warning::

   This module is currently in its initial release version.
   While feature-complete for its intended use case, it may still contain
   undetected bugs, edge-case issues, or performance bottlenecks.

   We do not recommend for use outside of Glo customer based at this time.


How it works
------------

A method describes its pipeline through a proxy. Calls on the proxy describe
stages; calls on ``self`` run as usual::

    class MagentoBackend(models.Model):
        _name = "magento.backend"
        _inherit = "pipeline.mixin"

        def fetch_orders(self):
            pipeline = self.pipeline()
            return pipeline.path(
                pipeline.with_delay()._download_orders().expand(),
                pipeline.with_delay()._import_order(),
            )

        def _download_orders(self, message):
            return self._magento_download_orders()

        def _import_order(self, order):
            self._magento_import_order(order)

Building a pipeline does nothing on its own - ``run`` starts it::

    backend.fetch_orders().run()
    backend.fetch_orders().run({"order_id": "100042"})

``with_delay()`` - contributed by the glue module (``pipeline_queue_job``) --
marks a stage to run in its own queued job, and is where its queue options go:
``channel``, ``priority``, ``eta``, ``identity_key`` and the rest, passed
straight through. A stage described *without* ``with_delay()`` runs inline, as a
continuation of the job that produced its input. So you choose, per stage, what
becomes a job and what rides along. (Core on its own runs everything inline; the
engine adds the deferral.)

``expand()`` splits a stage's result and sends each value on independently.
Together with the marker it controls fan-out: expand into a ``with_delay()``
stage gives one job per value - a single download fanning out into hundreds of
independent imports - while expand into an inline stage handles every value in
the one job. Pipelines are linear - fan-out yes, branching or joining no.

.. warning::

   **A stage that returns ``None`` ends its path - the successor never runs.**
   This is deliberate: return ``None`` to stop early (nothing to hand on). But
   it also means a stage with a *forgotten* ``return`` returns ``None`` and
   silently halts everything downstream. If a stage should continue the path, it
   must ``return`` the message the next stage needs - and that message is
   stored as a job argument, so keep it JSON-serialisable.

``run()`` returns the queued Job when the first stage is delayed, or the final
result when the whole pipeline is inline - the same distinction as
``with_delay().method()`` versus ``method()``.

Want to see a definition before you run it? ``to_mermaid()`` and ``to_dot()``
render it as a diagram.

Batteries included
------------------

``pipeline.tools`` carries the bits every file-based integration otherwise
re-invents: scanning and archiving files over any fsspec filesystem, reading and
writing CSV/XLS/XLSX rows, and splitting rows into batches. They are small,
explicit helpers you call - not a framework you plug into.

Two things to take from this, beyond the helpers themselves:

* **It is a pattern, not just a library.** Reusable pieces stay small, Odoo-free,
  and take their dependencies explicitly - a filesystem, a file handle - so
  they are easy to test and share. When your integration grows a reusable bit,
  write it the same way: a plain helper a stage calls, never another layer of
  framework.

* **Reach for fsspec at the filesystem boundary.** Anything that touches files
  should go through an fsspec filesystem rather than ``open()`` or a
  protocol-specific client. A stage written against fsspec is
  transport-agnostic: local today, SFTP or S3 tomorrow, with no code change --
  just a different filesystem handed in. It is our strong recommendation, and
  what the file helpers above assume.

Documentation
-------------

The ``docs/`` directory goes deeper:

* ``docs/tools.rst`` - the full ``pipeline.tools`` catalogue (files, row codecs
  and batching), and the details each helper hides.
* ``docs/csv.rst`` - a complete, annotated integration that picks up a CSV,
  groups it, and fans each group out to its own job.
* ``docs/email.rst`` - a recipe for starting a pipeline from an inbound email
  through Odoo's mail-alias gateway.

Under the hood
--------------

Each job stores its recordset, method names and input - never a frozen copy of
the graph. At the start of every job Pipeline re-reads your pipeline method, so
retried and in-flight jobs always run today's code, not yesterday's. A job is
one transaction spanning its deferred stage and every inline stage after it, up
to the next ``with_delay()`` boundary - so a retry re-runs that whole chain
atomically, with no half-finished commits in the middle. Everything else --
model, method, state, retries, errors - is what the engine (``queue_job``)
already tracks; core keeps no bookkeeping of its own. (The engine tags a run's
jobs with a shared group so they can be filtered together, but that lives in
``pipeline_queue_job``, not core.)

Triggers stay with the addon
----------------------------

Buttons, crons, webhooks and inbound email belong to the concrete integration,
using standard Odoo facilities::

    def action_fetch_orders(self):
        for backend in self:
            backend.fetch_orders().run()

Why not...
----------

**...connector_edi?** Our own EDI framework is a great fit for standardised,
high-volume EDI - backends, bindings, mappers and exchange records moving
through a formal lifecycle. Most of our integrations simply are not that. The
brief is usually "pick up this file, group it, create these records", it is
specific to one customer, and it changes often. Modelling that as exchange types
and mappers adds ceremony the job never needed, and spreads a single integration
across so many registered pieces that "what happens when a file arrives?"
becomes genuinely hard to answer. What we actually needed was a tidy way to
queue related jobs - so that is all Pipeline is. When a job really is strict EDI,
reach for ``connector_edi``; the rest of the time, Pipeline keeps out of your way.

**...code stored in the database?** It is tempting to make an integration
"configurable" by keeping its logic in ``code`` fields, server actions or
``safe_eval`` snippets. Please don't. Database code never sees git - no review,
no history, no tests - and two environments drift the moment someone edits one
of them. Running stored Python is also a real security risk: anyone who can
write that record can run code inside Odoo. Pipeline keeps behaviour in methods,
where it is reviewed, tested and debuggable, and keeps genuine configuration --
credentials, paths, schedules, filters - in ordinary fields.

None of this is enforced. If a particular integration truly needs
database-stored logic, it is free to build that in its own stages and own the
trade-off. Pipeline just never hands you that risk by default.
