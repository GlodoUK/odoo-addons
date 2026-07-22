pipeline_queue_job
==================

The queue_job engine for pipeline. Install it alongside ``pipeline`` to run stages
marked with ``with_delay()`` as background ``queue.job`` records.

pipeline core is engine-agnostic: it walks a pipeline, runs inline stages in the
current transaction, and hands each ``with_delay()`` stage to whatever engine is
installed through the ``_pipeline_dispatch`` seam. This module is that engine for
OCA ``queue_job``: it contributes the ``with_delay()`` marker (via a
``post_load`` hook) and enqueues each deferred stage with
``with_delay(**options)``, passing the stage's queue options - ``channel``,
``priority``, ``eta``, ``identity_key`` and the rest - straight through. Each
job carries a human description, and ``queue_job`` tracks the rest (model,
method, state, retries, errors).

Without an engine module, a pipeline that uses ``with_delay()`` raises when it
reaches a deferred stage; a fully inline pipeline needs no engine at all.
