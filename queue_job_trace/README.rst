===============
Job Queue Trace
===============

This module adds an opt-in **trace** to ``queue_job``: a correlation id
shared by every job spawned, directly or transitively, from the same
origin.

Unlike ``graph_uuid`` — which drives job dependencies and is built up
front — a trace carries no execution semantics. It is a pure lineage
tag, meant for observability: grouping, searching, and correlating a
flow of jobs with your own logs or with external systems.

Tracing is **opt-in**. Untraced jobs are unaffected and keep an empty
trace. Once a job is traced, any job it enqueues while running inherits
the trace automatically, so the whole tree of spawned jobs shares one
id.

.. IMPORTANT::
   This is an alpha version, the data model and design can change at any time without warning.

Usage
=====

Start a trace with the ``with_trace()`` helper, then enqueue as usual:

.. code:: python

   # mint a fresh trace id
   self.env["my.model"].with_trace().with_delay().step_one(...)

   # or use your own correlation id (e.g. a document name, an external request id)
   self.env["my.model"].with_trace("SO-2026-0042").with_delay().step_one(...)

Any job enqueued while ``step_one`` runs inherits the same trace, so a
pipeline built by tail-enqueueing (each job enqueues the next once it
knows its result) is captured end to end — even across models — with no
further wiring:

.. code:: python

   def step_one(self):
       partners = ...
       partners.with_delay().step_two()   # inherits step_one's trace

   def step_two(self):
       ...

Read the current trace from inside a running job, e.g. to log it:

.. code:: python

   trace = self.env["queue.job"]._current_trace()

On the job form, a **Trace** smart button and a **Trace** tab (a tree
view reusing the dependency-graph widget) show the whole flow. Jobs can
be grouped by trace in the list view, and ``record.cancel_trace()``
cancels every not-yet-finished job in the flow.
