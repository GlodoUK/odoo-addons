import inspect
import sys
from collections.abc import Iterable

from odoo import models

from ..pipeline import Pipeline, PipelineError


class PipelineMixin(models.AbstractModel):
    """Queue and monitor code-defined pipelines on a concrete Odoo record."""

    _name = "pipeline.mixin"
    _description = "Pipeline Pipeline Runner"

    def pipeline(self):
        """Return a Delayable-like pipeline proxy for this record."""
        self.ensure_one()
        definition_method = sys._getframe(1).f_code.co_name
        return Pipeline(self, definition_method)

    def _pipeline_pipeline(self, pipeline_method):
        """Re-derive the pipeline from its definition method and validate it.

        Called at the start of every job, so retried and in-flight work resolves
        against current Python code rather than a serialized copy of a graph.
        """
        self.ensure_one()
        definition = getattr(self, pipeline_method, None)
        if definition is None:
            raise PipelineError(
                f"Pipeline definition method {pipeline_method!r} is unavailable."
            )
        pipeline = definition()
        if not isinstance(pipeline, Pipeline):
            raise PipelineError(
                f"{self._name}.{pipeline_method}() must return a Pipeline."
            )
        pipeline.validate()
        return pipeline

    def _pipeline_start(self, pipeline_method, stage_names, message=None):
        """Start a pipeline from its root stage(s). A deferred root is dispatched
        to the engine (its handle returned); an inline root runs now, in the
        calling transaction, and returns its result."""
        self.ensure_one()
        pipeline = self._pipeline_pipeline(pipeline_method)
        results = [
            self._pipeline_enter(
                pipeline, pipeline_method, pipeline.stage(stage_name), message
            )
            for stage_name in stage_names
        ]
        return results[0] if len(results) == 1 else results

    def _pipeline_enter(self, pipeline, pipeline_method, stage, message):
        """Enter a stage: hand a deferred stage to the async engine, otherwise
        run it inline here, in the current transaction."""
        if stage.deferred:
            return self._pipeline_dispatch(pipeline_method, stage, message)
        return self._pipeline_advance(pipeline, pipeline_method, stage.name, message)

    def _pipeline_dispatch(self, pipeline_method, stage, message):
        """Run a deferred stage asynchronously - the async-engine seam.

        This is the *only* point that touches a job queue, and core provides no
        engine. Install an engine module (``pipeline_queue_job``) that overrides
        this and contributes the marker that defers a stage. A pipeline with no
        deferred stages never reaches here and needs no engine at all.
        """
        raise PipelineError(
            f"Stage {stage.name!r} is deferred to an async engine, but none is "
            f"installed. Install pipeline_queue_job (or another engine), or leave "
            f"the stage inline."
        )

    def _pipeline_run_stage(self, pipeline_method, stage_name, message):
        """Job entry point for a deferred stage: re-derive the pipeline, run the
        stage, then drive its inline continuation within this job."""
        pipeline = self._pipeline_pipeline(pipeline_method)
        return self._pipeline_advance(pipeline, pipeline_method, stage_name, message)

    def _pipeline_advance(self, pipeline, pipeline_method, stage_name, message):
        """Run one stage and continue into its successor for each output.

        An inline successor runs here, in this transaction; a deferred successor
        is dispatched to the engine as its own job - one per value when the
        current stage ``expand()``s. Returns the stage's own result, so the
        entry stage's return is what the job stores.
        """
        stage = pipeline.stage(stage_name)
        result = self._pipeline_call_stage(getattr(self, stage.method_name), message)
        successor = pipeline.successor(stage_name)
        if successor is None:
            return result
        for output in self._pipeline_outputs(stage, result):
            self._pipeline_enter(pipeline, pipeline_method, successor, output)
        return result

    @staticmethod
    def _pipeline_call_stage(method, message):
        """Run a stage, passing the upstream message only if it accepts one."""
        positional = (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        )
        accepts_message = any(
            parameter.kind in positional
            for parameter in inspect.signature(method).parameters.values()
        )
        return method(message) if accepts_message else method()

    @staticmethod
    def _pipeline_outputs(stage, result):
        """The values a stage hands to its successor - one normally, many when
        it ``expand()``s, none when it returns ``None``.

        Returning ``None`` ends the path: the successor never runs. This is
        deliberate (stop early with nothing to pass on), but note a stage with a
        forgotten ``return`` also returns ``None`` and so silently halts
        everything downstream - a stage meant to continue must return its
        message.
        """
        if result is None:
            return []
        if not stage.expand_output:
            return [result]
        if isinstance(result, (str, bytes)) or not isinstance(result, Iterable):
            raise PipelineError(
                f"Stage {stage.name!r} uses expand(), but returned "
                f"non-expandable {type(result).__name__}."
            )
        return result
