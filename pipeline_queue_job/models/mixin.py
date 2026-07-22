from odoo import models


class PipelineMixin(models.AbstractModel):
    """Drive pipeline' deferred stages through OCA queue_job.

    pipeline core is engine-agnostic: it runs inline stages in the current
    transaction and hands each ``with_delay()`` stage to ``_pipeline_dispatch``.
    This override makes that dispatch enqueue a ``queue.job`` whose entry point
    is core's own stage runner; ``queue_job`` tracks the rest (model, method,
    state, retries, errors).
    """

    _inherit = "pipeline.mixin"

    def _pipeline_dispatch(self, pipeline_method, stage, message):
        return self.with_delay(
            **self._pipeline_delay_options(pipeline_method, stage)
        )._pipeline_run_stage(pipeline_method, stage.name, message)

    def _pipeline_delay_options(self, pipeline_method, stage):
        """queue_job ``with_delay`` options for a deferred stage: the options the
        pipeline gave it (``channel``, ``priority``, ``eta``, ``identity_key``,
        ...), defaulting a human description when none was set."""
        options = dict(stage.dispatch_options)
        options.setdefault(
            "description",
            self.env._(
                "%(name)s: %(method)s -> %(stage)s",
                name=self.display_name,
                method=pipeline_method,
                stage=stage.name,
            ),
        )
        return options
