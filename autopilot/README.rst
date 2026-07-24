=========
autopilot
=========

.. caution::
   **Early Access (Alpha Status)**

   This module is actively under development and is intended primarily for
   **Glo deployments** while we refine feature stability.

   As with any early-stage feature, functionality may evolve.

   That said, this module is the intended replacement for our ``connector_edi`` suite
   of modules and offers a vast simplification - we do not anticipate its removal.

   However, Glo stands fully behind our customers: should this module change direction
   or be phased out, Glo will work with you on a migration path.

Toolkit for building lightweight, bespoke Odoo connectors - the kind that poll a
folder, push a file, or react to a record and call out to a third party.

It exists because the alternatives are both wrong for this: a full EDI/connector
framework is too heavy, and hand-rolling each connector means re-writing the same
plumbing (wire a cron, sweep a folder, react to an event, show up in a menu) every
time. autopilot is the shared *mechanism* for that plumbing, so a connector stays
a small module of bespoke logic.

It is deliberately **not** a configurable engine. There is no in-database node
graph, no ``safe_eval`` code fields, no envelope/message/codec records. What a
connector does lives in **code**; only genuine operational parameters (a poll
interval, an on/off switch) are database fields.

autopilot has three parts:

1. **Triggers** - a mixin + decorators that turn "run this method on a schedule /
   when this happens" into self-managed ``ir.cron`` / ``base.automation`` records.
2. **Tools** - Odoo-free ETL helpers (fsspec file ops + row codecs).
3. **The app** - a shared "Autopilot" menu connectors hang themselves under.

A connector composes these; it depends on ``autopilot`` and stays bespoke.

Triggers
========

Inherit ``autopilot.mixin``, declare a ``Many2one`` per trigger, and decorate the
methods you want driven:

.. code-block:: python

    from odoo import fields, models
    from odoo.addons.autopilot import cron, automation


    def _due_for_export(backend):
        # A plain function reference is resolved just like a lambda - called
        # with the record. Use one when the rule is worth naming or reusing.
        return backend.active and bool(backend.export_path)


    class AcmeBackend(models.Model):
        _name = "acme.backend"
        _inherit = ["autopilot.mixin"]

        active = fields.Boolean(default=True)
        partner_id = fields.Many2one("res.partner")
        export_path = fields.Char()
        poll_every = fields.Integer(default=15)
        poll_unit = fields.Selection([...], default="minutes")
        dispatch_cron_id = fields.Many2one("ir.cron", copy=False)
        order_automation_id = fields.Many2one("base.automation", copy=False)

        # interval from fields (record-tunable); active from a function reference.
        @cron("dispatch_cron_id",
              interval_number="poll_every", interval_type="poll_unit",
              active=_due_for_export)
        def _dispatch(self):
            ...

        # domain computed per-record with a lambda, scoped to this backend.
        @automation("sale.order", "order_automation_id",
                    trigger="on_create_or_write",
                    domain=lambda backend: [("partner_id", "=", backend.partner_id.id)],
                    delay=True)
        def _on_order(self, records):
            ...

How it works
------------

* The decorators are **pure markers** (like ``@api.depends``) - they only stash
  metadata on the method. Nothing runs at import time.
* On **create/write**, the mixin scans the model's decorated methods and, for
  each, creates or updates the backing record (an ``ir.cron`` for ``@cron``, a
  ``base.automation`` + server action for ``@automation``), storing it in the
  ``Many2one`` the decorator names. **That field is the link** - the backing
  record is visible on the form, queryable, and cleaned up on unlink.
* Each backend gets its **own** backing records; the generated code calls the
  decorated method directly on that record, e.g.
  ``env['acme.backend'].browse(5)._dispatch()``.
* On **unlink**, the backing records are removed.

Value resolution
----------------

``interval_number`` / ``interval_type`` / ``active`` / ``domain`` are resolved
**per record** at sync time, in order:

1. a **callable** ``(record) -> value`` is called (e.g.
   ``active=lambda r: r.state == 'live'``, or a domain scoped to the record);
2. a value that **names a field** is read from that field (so the schedule is
   tunable from the backend's own form, no code change);
3. anything else is a **literal**.

Because a lambda is opaque, a spec carrying one re-syncs on every write; a plain
field reference re-syncs only when that field changes.

Running as a queued job (``delay``)
-----------------------------------

Pass ``delay=True`` (or a dict of ``with_delay`` options) to run the method as a
``queue_job`` instead of inline. This matters most for ``@automation``: a rule
fires inside the *triggering user's transaction*, so anything hitting a third
party should run after commit, in a job.


Tools
=====

``autopilot.tools`` is a set of Odoo-free, unit-testable helpers a connector's
methods call directly (moved verbatim from the old ``base_etl``):

* ``files`` - drive an fsspec filesystem: ``glob``, ``archive``, ``sweep``
  (glob + archive, the one-shot "claim the batch" primitive), and
  ``fsspec_providers`` for a transport ``Selection``.
* ``csv`` / ``xls`` / ``xlsx`` - row codecs with one interface,
  ``read_rows(handle)`` / ``write_rows(handle, rows)``; ``codec_for(name)`` picks
  one by file extension.
* ``batch`` - ``batched(rows, size)`` for fan-out.

.. code-block:: python

    from odoo.addons.autopilot import tools

    fs = fsspec.filesystem("sftp", **opts)          # the connector owns the fs
    for path in tools.files.sweep(fs, "/in/*.csv", "/in/processed"):
        with fs.open(path, "rb") as handle:
            rows = tools.codec_for(path).read_rows(handle)

Nothing here imports Odoo - the tools *drive* a filesystem the caller builds, and
are testable on an in-memory handle. Keep them that way: no models, no ``odoo``
import under ``tools/``.


The app
=======

autopilot ships an **"Autopilot" app menu** and a landing that is a static
explainer (so opening the app lands somewhere meaningful, not an arbitrary
connector). autopilot on its own does nothing.

Under the app it provides a **Connections** submenu; connectors parent their
**own** menus - a normal list/kanban of their backend model, gated by their own
groups - there (not directly under the app root, so the top level stays tidy as
connectors are added):

.. code-block:: xml

    <record id="action_acme_backend" model="ir.actions.act_window">
      <field name="name">Acme Backends</field>
      <field name="res_model">acme.backend</field>
      <field name="view_mode">list,form</field>
    </record>

.. code-block:: xml

    <menuitem id="menu_acme_backend"
      name="Acme"
      parent="autopilot.menu_autopilot_connections"
      action="action_acme_backend"
      groups="base.group_user"/>

The app also carries **Scheduled Actions** and **Automation Rules** shortcuts
(the standard ``ir.cron`` / ``base.automation`` views, for admins) so the
primitives autopilot manages are reachable without digging through Settings >
Technical.

**Access** to backends is enforced entirely by the concrete models themselves
(their own ACL / record rules); autopilot adds no access layer. There is
deliberately no cross-connector status dashboard - if a rich at-a-glance view is
ever wanted, a per-connector kanban dashboard on the connector's own model is the
place for it.

Design principles
=================

* **Config in code, not a DB UI.** Behaviour is decorated methods; only
  operational knobs (interval, active) are fields.
* **Mechanism, not a framework.** The mixin holds no fields and dictates no
  structure; connectors stay bespoke.
* **The concrete model is the source of truth** for data *and* access.
* **Keep it Simple.** ``tools`` should stay small and Odoo-free. Heavy or optional
  integrations (LLM, SFTP, S3 backends, ...) belong in their own sibling modules a
  connector composes - never in autopilot itself.

Why not a framework?
====================

autopilot deliberately builds on Odoo's other primitives (``ir.cron`` /
``base.automation`` / ``queue_job``) rather than adopting a connector framework.

**...the OCA** ``connector`` **framework?** ``connector`` earns its keep on large,
bidirectional, high-volume syncs against a stable external API - many record
types, durable external-id bindings, mappings that rarely change. It pays for
that with real machinery: a component registry (``_collection`` / ``_apply_on`` /
``_usage``), a binding (shadow) model per synced record, and mapper/synchroniser
layers. The cost is indirection - to answer "what runs when this happens?" you
trace component discovery instead of reading a method - and it only amortises
when the integration is big, bidirectional and long-lived. Ours usually are not:
one customer, one-directional, changing often, needing no durable binding. For
that shape the framework is nearly all ceremony.

**...connector_edi (our own EDI framework)?** ``connector_edi`` was intended for
standardised, high-volume EDI - backends, bindings, mappers and exchange records
moving through a formal lifecycle. Most of our integrations simply are not that,
and modelling them as exchange types and mappers adds ceremony the job never
needed while spreading one integration across so many registered pieces that
"what happens when a file arrives?" gets hard to answer. It also inadvertantly
encouraged in database ``code`` / ``safe_eval`` fields that never see version control
and drift between environments.

**...a lighter connector_edi, then?** That was the brief - and the early designs
kept the framework instinct: a ``protocol`` / ``behaviour`` switch of pluggable
strategies, an IFTTT-style trigger→action recipe engine, a flow of stages driving
a document through a lifecycle, configuration templates, a shadow "backend"
registry with a cross-connector dashboard and delegated rules. Each collapsed the
same way: the framework-shaped parts were already Odoo primitives (``ir.cron`` /
``base.automation``, the order->dispatch->invoice lifecycle Odoo already owns and
sequences, ``queue_job``, the model's own access rules) or re-implemented them
worse, while the reusable remainder was tiny - declaratively wiring those
triggers, plus a few file/codec helpers. Everything configurable in between only
re-added the in-DB config and indirection we were escaping. So the lighter
``connector_edi`` is not a framework at all; it is autopilot - the primitives made
convenient, with the bespoke logic left in code.

**...a pipeline DSL?** An earlier iteration described integrations as a graph of
stages, with each stage passing the output to the next. Whilst it was helpful seeing the
whole chain up front (note that a named ``queue_job`` chain requires all args at
point-of-queue) it was actually *more* harmful than beneficial.

**...why anything at all?** We need *something* to prevent rebuilding the same things
over and over again, but with the realisation it's usually the most basic of parts.
The parts we actually want - a scheduled/reactive trigger and a job queue - are just
``ir.cron``, ``base.automation``, ``queue_job`` which autopilot exposes directly as thin
decorators instead of stacking a component/binding/mapper layer on top.
