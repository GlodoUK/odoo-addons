"""Marker decorators that declare, on a method, the automation that should
drive it.

These are *pure markers* - exactly like ``@api.depends``, they only stash
metadata on the function and never run anything themselves. The
``autopilot.mixin`` (see ``models/autopilot_mixin.py``) scans a model for
decorated methods on create/write and materialises the backing ``ir.cron`` /
``base.automation`` records, keeping them in step with the record's fields.

Each decorator names a ``field`` on the model: a ``Many2one`` the mixin stores
the backing record in. That field *is* the link - the reference lives on the
connector itself (visible in its form, queryable, cleaned up on unlink), so
there is no separate bookkeeping model. The connector declares the field; one
decorator per field::

    class SilverxBackend(models.Model):
        _name = "silverx.backend"
        _inherit = ["autopilot.mixin"]

        dispatch_cron_id = fields.Many2one("ir.cron", copy=False)
        order_automation_id = fields.Many2one("base.automation", copy=False)

        @cron("dispatch_cron_id",
              interval_number="poll_every", interval_type="poll_unit")
        def _dispatch(self): ...

        @automation("sale.order", "order_automation_id",
                    trigger="on_create_or_write", delay=True)
        def _on_order(self, records): ...

The generated ``ir.cron`` / ``base.automation`` calls the decorated method
*directly* - ``record._dispatch()`` / ``record._on_order(records)``.

Value resolution
----------------
``interval_number`` / ``interval_type`` / ``active`` / ``domain`` are resolved
per-record at sync time, in this order: **a callable is called with the record;
a value that names a field is read from that field; anything else is used
literally.** So a plain default works with no fields at all, naming a field
makes it record-tunable from the connector's own form, and a lambda computes it
- e.g. ``active=lambda r: r.state == "live"`` or a domain scoped to the record,
``domain=lambda r: [("partner_id", "=", r.partner_id.id)]``.

A lambda is opaque to field-dependency tracking, so a connector carrying one
re-syncs its backing records on *every* write (not only when a named field
changes). Prefer a plain field reference where a lambda is not needed.

Running off-thread (``delay``)
------------------------------
``delay`` (opt-in) runs the method as a ``queue_job`` job instead of inline.
Pass ``True`` for defaults, or a dict of ``with_delay`` options to forward
(``channel``, ``priority``, ``identity_key``, ``max_retries``, ...). This
matters most for ``@automation``: a rule fires inside the *triggering user's
transaction*, so a method that hits an external system should run after commit,
in a job - not block the request or ride its rollback. Options are baked into
the generated code as a literal, so keep them to literals (a string
``identity_key`` is fine, the ``identity_exact`` sentinel is not). Note the
backing record is per-connector-record, so a *static* ``identity_key`` would
collapse jobs across records/firings - include something record-specific if you
set one.
"""


def cron(
    field,
    interval_number=5,
    interval_type="minutes",
    active="active",
    name=None,
    delay=None,
):
    """Declare that the decorated method should be run by an ``ir.cron``.

    ``field`` is the name of a ``Many2one("ir.cron")`` on the model where the
    backing cron is stored. ``interval_number`` / ``interval_type`` / ``active``
    are each a callable ``(record) -> value``, a field name (resolved
    per-record), or a literal; ``interval_type`` resolves to an ``ir.cron``
    value (``minutes``/``hours``/``days``/``weeks``/``months``). ``name``
    overrides the generated cron name. ``delay`` (see module docstring) runs the
    method as a ``queue_job`` job. The decorated method takes no arguments
    beyond ``self``.
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
    """Declare that the decorated method should be run by a ``base.automation``
    watching ``model``.

    ``model`` is the *target* model whose records fire the rule (e.g.
    ``"sale.order"``) - not this connector's model. ``field`` is the name of a
    ``Many2one("base.automation")`` on the model where the backing rule is
    stored. ``trigger`` is a ``base.automation`` trigger (default
    ``on_create_or_write``); ``domain`` is the rule's filter - a domain string,
    a field name, or a callable ``(record) -> domain`` for a record-scoped
    filter (a returned list is stringified for ``filter_domain``). ``active`` is
    a callable / field name / literal; ``name`` overrides the generated name.
    ``delay`` (see module docstring) runs the method as a ``queue_job`` job -
    strongly recommended here, since the rule fires in the triggering user's
    transaction. The decorated method receives the triggered records:
    ``def _on_order(self, records): ...``.
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
