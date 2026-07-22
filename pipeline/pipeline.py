"""Registry-free descriptions of Odoo method pipelines."""

import json


class PipelineError(Exception):
    """Base error for invalid pipeline definitions or execution."""


class PipelineValidationError(PipelineError):
    """Raised when a pipeline is structurally invalid."""


class Stage:
    """A model method described through a Pipeline proxy."""

    def __init__(self, pipeline, method):
        self.pipeline = pipeline
        self.name = method.__name__
        self.method_name = method.__name__
        self.expand_output = False
        # Whether crossing into this stage is dispatched to the async engine
        # (its own unit of work) rather than run inline. Core has no way to set
        # this - an engine module contributes a marker (e.g. pipeline_queue_job's
        # ``with_delay``) that flips it and stores engine-specific options here.
        self.deferred = False
        self.dispatch_options = {}

    def expand(self):
        """Create one successor invocation per value returned by this stage."""
        self.expand_output = True
        return self


class Pipeline:
    """A current, code-defined set of one-way method stages."""

    def __init__(self, records, definition_method):
        records.ensure_one()
        self.records = records
        self.definition_method = definition_method
        self._stages = {}
        self._successors = {}
        self._predecessors = {}

    def __getattr__(self, method_name):
        method = getattr(self.records, method_name, None)
        if not callable(method):
            raise AttributeError(method_name)

        def describe_stage():
            return self._stage(method)

        return describe_stage

    def _stage(self, method):
        name = getattr(method, "__name__", None)
        if not callable(method) or not name:
            raise PipelineValidationError(
                f"Pipeline {self.definition_method!r} expects an Odoo model method, "
                f"got {method!r}."
            )
        stage = self._stages.get(name)
        if stage is None:
            stage = Stage(self, method)
            self._stages[name] = stage
        return stage

    def _coerce_stage(self, value):
        if isinstance(value, Stage):
            if value.pipeline is not self:
                raise PipelineValidationError(
                    "Stages from different pipelines cannot share a path."
                )
            return value
        return self._stage(value)

    def _add_edge(self, source, target):
        existing = self._successors.get(source.name)
        if existing is not None and existing != target.name:
            raise PipelineValidationError(
                f"Stage {source.name!r} already continues to {existing!r}; "
                "pipelines support fan-out of values, not branching topology."
            )
        predecessor = self._predecessors.get(target.name)
        if predecessor is not None and predecessor != source.name:
            raise PipelineValidationError(
                f"Stage {target.name!r} already follows {predecessor!r}; "
                "pipelines do not provide convergence or join semantics."
            )
        self._successors[source.name] = target.name
        self._predecessors[target.name] = source.name

    def path(self, *stages):
        """Add one linear path and return this pipeline."""
        if not stages:
            raise PipelineValidationError(
                f"Pipeline {self.definition_method!r} path() needs a stage."
            )
        current = self._coerce_stage(stages[0])
        for value in stages[1:]:
            successor = self._coerce_stage(value)
            self._add_edge(current, successor)
            current = successor
        return self

    @property
    def roots(self):
        return [name for name in self._stages if name not in self._predecessors]

    @property
    def stage_names(self):
        return list(self._stages)

    def stage(self, name):
        try:
            return self._stages[name]
        except KeyError:
            raise PipelineError(
                f"Pipeline {self.definition_method!r} no longer contains "
                f"stage {name!r}. "
                "Start a new run or restore that method name before retrying."
            ) from None

    def successor(self, name):
        target = self._successors.get(name)
        return self._stages[target] if target else None

    def validate(self):
        if not self._stages:
            raise PipelineValidationError(
                f"Pipeline {self.definition_method!r} contains no stages."
            )
        expanded_terminals = [
            name
            for name in self._stages
            if self._stages[name].expand_output and name not in self._successors
        ]
        if expanded_terminals:
            raise PipelineValidationError(
                f"Pipeline {self.definition_method!r} expands terminal stages "
                f"{expanded_terminals}; expand() requires a successor."
            )
        visited = set()
        visiting = set()

        def visit(name):
            if name in visiting:
                raise PipelineValidationError(
                    f"Pipeline {self.definition_method!r} contains a cycle at {name!r}."
                )
            if name in visited:
                return
            visiting.add(name)
            successor = self._successors.get(name)
            if successor:
                visit(successor)
            visiting.remove(name)
            visited.add(name)

        for name in self._stages:
            visit(name)
        return True

    def run(self, message=None):
        self.validate()
        return self.records._pipeline_start(
            pipeline_method=self.definition_method,
            stage_names=self.roots,
            message=message,
        )

    def to_mermaid(self):
        lines = ["graph TD"]
        for source, target in self._successors.items():
            label = "-->|each|" if self._stages[source].expand_output else "-->"
            lines.append(f"    {source} {label} {target}")
        connected = set(self._successors) | set(self._successors.values())
        lines.extend(f"    {name}" for name in self._stages if name not in connected)
        return "\n".join(lines)

    def to_dot(self):
        """Return this pipeline as Graphviz DOT source."""
        lines = ["digraph pipeline {", "    rankdir=LR;"]
        lines.extend(f"    {json.dumps(name)};" for name in self._stages)
        for source, target in self._successors.items():
            attributes = ' [label="each"]' if self._stages[source].expand_output else ""
            lines.append(
                f"    {json.dumps(source)} -> {json.dumps(target)}{attributes};"
            )
        lines.append("}")
        return "\n".join(lines)
