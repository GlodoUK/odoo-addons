import sys

from odoo.tests.common import TransactionCase

from odoo.addons.pipeline.pipeline import Pipeline, PipelineValidationError


class FakeRecords:
    def ensure_one(self):
        return self

    def pipeline(self):
        return Pipeline(self, sys._getframe(1).f_code.co_name)

    def first(self, message):
        return message

    def second(self, message):
        return message

    def third(self, message):
        return message

    def poll(self):
        pipeline = self.pipeline()
        return pipeline.path(
            pipeline.first().expand(),
            pipeline.second(),
            pipeline.third(),
        )

    def _pipeline_start(self, **values):
        self.started = values
        return values


class TestPipeline(TransactionCase):
    def setUp(self):
        super().setUp()
        self.records = FakeRecords()

    def test_linear_pipeline_and_expand(self):
        pipeline = self.records.poll()
        self.assertEqual(pipeline.definition_method, "poll")
        self.assertEqual(pipeline.stage_names, ["first", "second", "third"])
        self.assertEqual(pipeline.roots, ["first"])
        self.assertTrue(pipeline.stage("first").expand_output)
        self.assertEqual(pipeline.successor("first").name, "second")
        self.assertEqual(pipeline.successor("second").name, "third")
        self.assertTrue(pipeline.validate())

    def test_run_uses_definition_method(self):
        self.records.poll().run({"seed": 1})
        self.assertEqual(
            self.records.started,
            {
                "pipeline_method": "poll",
                "stage_names": ["first"],
                "message": {"seed": 1},
            },
        )

    def test_stages_are_inline_by_default(self):
        # Core has no marking verb, so every stage is inline until an engine
        # module defers it.
        stage = self.records.pipeline().first()
        self.assertFalse(stage.deferred)
        self.assertEqual(stage.dispatch_options, {})

    def test_path_returns_pipeline(self):
        pipeline = self.records.pipeline()
        self.assertIs(
            pipeline.path(pipeline.first(), pipeline.second()),
            pipeline,
        )

    def test_branching_is_rejected(self):
        pipeline = self.records.pipeline()
        first = pipeline.first()
        pipeline.path(first, pipeline.second())
        with self.assertRaisesRegex(PipelineValidationError, "not branching"):
            pipeline.path(first, pipeline.third())

    def test_cycle_is_rejected(self):
        pipeline = self.records.pipeline()
        pipeline.path(pipeline.first(), pipeline.second(), pipeline.first())
        with self.assertRaisesRegex(PipelineValidationError, "cycle"):
            pipeline.validate()

    def test_convergence_is_rejected(self):
        pipeline = self.records.pipeline()
        pipeline.path(pipeline.first(), pipeline.third())
        with self.assertRaisesRegex(PipelineValidationError, "join semantics"):
            pipeline.path(pipeline.second(), pipeline.third())

    def test_expanded_terminal_is_rejected(self):
        pipeline = self.records.pipeline()
        pipeline.path(pipeline.first().expand())
        with self.assertRaisesRegex(PipelineValidationError, "requires a successor"):
            pipeline.validate()

    def test_mermaid_shows_expand(self):
        diagram = self.records.poll().to_mermaid()
        self.assertIn("first -->|each| second", diagram)
        self.assertIn("second --> third", diagram)

    def test_dot_shows_stages_and_expand(self):
        dot = self.records.poll().to_dot()
        self.assertIn('"first";', dot)
        self.assertIn('"first" -> "second" [label="each"];', dot)
        self.assertIn('"second" -> "third";', dot)


class TestStageDispatch(TransactionCase):
    def _call(self, method, message="msg"):
        return self.env["pipeline.mixin"]._pipeline_call_stage(method, message)

    def test_message_is_passed_when_stage_accepts_it(self):
        self.assertEqual(self._call(lambda message: message), "msg")

    def test_message_is_dropped_when_stage_takes_no_argument(self):
        self.assertEqual(self._call(lambda: "no-arg"), "no-arg")

    def test_var_positional_stage_receives_message(self):
        self.assertEqual(self._call(lambda *args: args), ("msg",))
