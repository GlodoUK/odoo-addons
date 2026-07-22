"""The ``with_delay`` marking verb pipeline core deliberately lacks.

pipeline core knows only that a stage may be *deferred* to an engine; it offers no
way to mark one. This engine contributes that: describing a stage through
``pipeline.with_delay(**options)`` defers it and attaches the queue_job options.
It is bolted onto core's ``Pipeline`` by this module's ``post_load`` hook, so a
core-only install never gains the verb (and runs everything inline).
"""


class _DelayedStages:
    """Proxy returned by ``Pipeline.with_delay``: accessing a model method on it
    describes that stage as deferred, carrying the queue_job options."""

    def __init__(self, pipeline, options):
        self._pipeline = pipeline
        self._options = options

    def __getattr__(self, method_name):
        method = getattr(self._pipeline.records, method_name, None)
        if not callable(method):
            raise AttributeError(method_name)

        def describe_stage():
            stage = self._pipeline._stage(method)
            stage.deferred = True
            stage.dispatch_options = self._options
            return stage

        return describe_stage


def with_delay(self, **options):
    """Describe the next stage as running in its own queued job.

    ``options`` are passed straight to queue_job's ``with_delay`` --
    ``priority``, ``eta``, ``channel``, ``identity_key``, ``max_retries``,
    ``description`` -- so this is the one explicit place a stage's queueing is
    configured. Stages described without it run inline, as a continuation of the
    job that produced their input.
    """
    return _DelayedStages(self, options)
