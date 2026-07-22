import sys

from odoo.tests.common import TransactionCase

from odoo.addons.pipeline.pipeline import Pipeline


class _Fake:
    """A stand-in record just rich enough to describe a pipeline."""

    def ensure_one(self):
        return self

    def pipeline(self):
        return Pipeline(self, sys._getframe(1).f_code.co_name)

    def download(self, message):
        return message


class TestWithDelay(TransactionCase):
    def _pipeline(self):
        return _Fake().pipeline()

    def test_with_delay_is_patched_onto_core_pipeline(self):
        # The engine contributes the marker via post_load.
        self.assertTrue(hasattr(Pipeline, "with_delay"))

    def test_with_delay_defers_stage_and_carries_options(self):
        stage = (
            self._pipeline().with_delay(channel="root.import", priority=5).download()
        )
        self.assertTrue(stage.deferred)
        self.assertEqual(
            stage.dispatch_options, {"channel": "root.import", "priority": 5}
        )
        # expand() still chains on a deferred stage.
        self.assertTrue(stage.expand().expand_output)

    def test_stage_without_with_delay_is_inline(self):
        stage = self._pipeline().download()
        self.assertFalse(stage.deferred)
        self.assertEqual(stage.dispatch_options, {})
