"""Markers, like ``@api.depends``. They only tag the method;
``autopilot.mixin`` turns them into ``ir.cron`` and ``base.automation``
records. See the README.

Watch out with ``delay``. Its options are written into the generated code, so
keep them literal: a string ``identity_key``, not ``identity_exact``. Each
connector record gets its own trigger, so a fixed ``identity_key`` would merge
jobs across records. Make it record-specific.
"""


def cron(
    field,
    interval_number=5,
    interval_type="minutes",
    active="active",
    name=None,
    delay=None,
):
    """Run the method from an ``ir.cron`` stored in the Many2one ``field``.

    ``interval_number`` / ``interval_type`` / ``active``: a callable
    ``(record) -> value``, a field name, or a literal. ``delay``: ``True`` or
    ``with_delay`` options, to run it as a queued job.
    """

    def deco(func):
        specs = list(getattr(func, "_autopilot_crons", ()))
        specs.append(
            {
                "field": field,
                "interval_number": interval_number,
                "interval_type": interval_type,
                "active": active,
                "name": name,
                "delay": delay,
            }
        )
        func._autopilot_crons = tuple(specs)
        return func

    return deco


def automation(
    model,
    field,
    trigger="on_create_or_write",
    domain="[]",
    active="active",
    name=None,
    delay=None,
):
    """Run the method from a ``base.automation`` on ``model`` (the watched
    model, e.g. ``"sale.order"``, not the connector's), stored in the
    Many2one ``field``. The method gets the triggering records.

    ``domain`` / ``active``: a callable ``(record) -> value``, a field name, or
    a literal. Use ``delay``: the rule runs inside the triggering user's
    transaction, so anything calling out should wait for the commit.
    """

    def deco(func):
        specs = list(getattr(func, "_autopilot_automations", ()))
        specs.append(
            {
                "model": model,
                "field": field,
                "trigger": trigger,
                "domain": domain,
                "active": active,
                "name": name,
                "delay": delay,
            }
        )
        func._autopilot_automations = tuple(specs)
        return func

    return deco
