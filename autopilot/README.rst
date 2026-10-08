=========
autopilot
=========

.. caution::
   **Early Access (Alpha Status)**

   This module is actively under development and is intended primarily for
   **Glo deployments** while we refine feature stability.

   As with any early-stage feature, functionality may evolve.

   That said, this module is the intended replacement for our ``connector_edi``
   suite of modules and offers a vast simplification. We do not anticipate its
   removal.

   However, Glo stands fully behind our customers: should this module change
   direction or be phased out, Glo will work with you on a migration path.

The toolkit for small, bespoke Odoo connectors: the kind that poll a folder,
send a file, or react to a record and call a third party.

Every connector needs the same plumbing. A schedule, a folder to sweep, a
reaction to an event, somewhere to store a password, a place in the menu.
autopilot provides that once, so each connector is a short module of its own
logic. It is not a configurable engine. What a connector does lives in code,
under version control. Only real operating settings, such as how often to
poll, are fields.

It gives you:

* **Triggers**: decorators that turn a method into a self-managed scheduled
  action or automation rule.
* **Tools**: Odoo-free helpers for moving files and reading or writing rows.
* **Connections**: one shared, secure place for every file endpoint.
* **Activity**: every connector's files and orders, and their states, in one
  list.
* **The app**: Integrations & Connections, where connectors live.

Triggers
========

Inherit ``autopilot.mixin``, add a ``Many2one`` per trigger, and decorate the
methods to run:

.. code-block:: python

    from odoo import fields, models
    from odoo.addons.autopilot import automation, cron


    class AcmeBackend(models.Model):
        _name = "acme.backend"
        _inherit = ["autopilot.mixin"]

        active = fields.Boolean(default=True)
        partner_id = fields.Many2one("res.partner")
        poll_every = fields.Integer(default=15)
        poll_unit = fields.Selection([...], default="minutes")
        dispatch_cron_id = fields.Many2one("ir.cron", copy=False)
        order_automation_id = fields.Many2one("base.automation", copy=False)

        @cron("dispatch_cron_id", interval_number="poll_every",
              interval_type="poll_unit")
        def _dispatch(self):
            ...

        @automation("sale.order", "order_automation_id",
                    domain=lambda backend: [("partner_id", "=", backend.partner_id.id)],
                    delay=True)
        def _on_order(self, records):
            ...

Each backend record gets its own scheduled action or automation rule, kept in
step as the record changes and removed with it. The ``Many2one`` is the link,
so you can see it on the form.

``interval_number``, ``interval_type``, ``active`` and ``domain`` each take a
literal, a field name (so it can be tuned from the form) or a function of the
record. A function can't be inspected, so a backend using one re-syncs on every
write.

``delay=True`` (or a dict of ``with_delay`` options) runs the method as a
queued job. Use it for automations: they run inside the user's save, so
anything calling out should wait for the commit.

Tools
=====

``autopilot.tools`` never imports Odoo, so it can be tested on an in-memory
file. Keep it that way.

* ``files``: ``glob``, ``archive``, ``sweep`` (claim a batch by moving it
  aside), ``opened`` (write, creating the folder) and ``render_path`` for
  ``{datetime:%Y}`` and ``{record.name}`` tokens in a configured path.
* ``csv``, ``xls``, ``xlsx``: ``read_rows(handle)`` and
  ``write_rows(handle, rows)``. ``codec_for(path)`` picks one by extension.
* ``ssh``: SFTP keys loaded in memory, and host-key pinning.
* ``batch``: ``batched(rows, size)``.

Connections
===========

``autopilot.connection`` is a file endpoint shared by every connector. A
backend points at one and keeps its own paths:

.. code-block:: python

    from odoo.addons.autopilot import tools

    connection_id = fields.Many2one("autopilot.connection", ondelete="restrict")

    def _import(self):
        for path in self.connection_id._sweep("/in/*.csv", "/in/done"):
            with self.connection_id._open(path) as handle:
                rows = tools.codec_for(path).read_rows(handle)

Administrators manage them under **Integrations & Connections > Connections**.
Everyone else can read them. A connection still in use can't be archived.

Providers: local folders, FTP, SFTP, Amazon S3 and S3-compatible stores, Google
Cloud Storage, Azure Blob Storage, HTTP(S) and Google Drive. Each has its own
fields. **Advanced Options** take anything else as JSON.

* **Credentials are write-only.** They're checked on save, stored for
  administrators only and never sent back to the browser. Keys stay in memory.
* **SFTP host keys can be pinned.** Test Connection pins the server's key the
  first time, so a server swapped in later is refused.

To add a provider, ``selection_add`` on ``protocol``, write
``_fsspec_kwargs_<protocol>(self, secrets)`` and add a page to the form.

Moving to shared connections
----------------------------

``_from_legacy(protocol, storage_options, company_id)`` turns old per-backend
JSON settings into a connection. ``autopilot.upgrade.move_connections`` moves
a connector's own connection model across, credentials and all. Call it from a
pre-migration, with autopilot updated in the same run:

.. code-block:: python

    from odoo.addons.autopilot.upgrade import move_connections


    def migrate(cr, version):
        move_connections(cr, "acme.connection", [("acme_backend", "connection_id")])

Activity
========

**Integrations & Connections > Activity** lists every connector's files,
orders and deliveries with a shared status: Draft, Pending, Error, Done or
Cancelled. Filter on Error to see everything that needs a hand. Click a row to
open the record, or Retry or Cancel it where the connector allows.

Nothing is copied. A model takes part by returning its own SELECT, usually via
``_source_select``:

.. code-block:: python

    @api.model
    def _autopilot_activity_query(self):
        return self.env["autopilot.activity"]._source_select(
            self,
            backend="backend_id",
            company="company_id",
            state="state",
            status={"pending": "pending", "done": "done", "error": "error"},
            error="error_message",
        )

Any argument can be an ``SQL`` expression instead of a field. Optional hooks:
``_autopilot_activity_state_labels()``, ``_autopilot_activity_retry()`` and
``_autopilot_activity_cancel()``. Activity is for administrators. Opening a
row applies the record's own access rules.

The app
=======

**Integrations & Connections** opens on Activity for administrators, or the
first connector a user can see. Connectors add their menu under
``autopilot.menu_autopilot_connections``, gated by their own groups:

.. code-block:: xml

    <menuitem id="menu_acme"
      name="Acme"
      parent="autopilot.menu_autopilot_connections"
      action="action_acme_backend"
      groups="base.group_user"/>

Administrators also get shortcuts to Scheduled Actions and Automation Rules.
Access to backends is the connector's own: autopilot adds no access layer.

Why not a framework?
====================

The OCA ``connector`` framework and our own ``connector_edi`` earn their keep
on large, two-way, long-lived integrations. Most of ours are one customer, one
direction and change often. For those, component registries, binding models,
mappers and in-database code add indirection: "what happens when a file
arrives?" gets hard to answer, and code in the database drifts between
environments.

Everything a framework would add is already in Odoo: ``ir.cron``,
``base.automation``, ``queue_job``, the order to delivery to invoice lifecycle
and each model's access rules. autopilot just makes them convenient, and leaves
the bespoke logic in code where you can read it.

* **Config in code.** Behaviour is decorated methods. Only operating settings
  are fields.
* **Mechanism, not framework.** The mixin adds no fields and no structure.
* **Keep tools small.** Heavy or optional integrations belong in their own
  modules.
