==============
autopilot_sale
==============

.. caution::
   **Early Access (Alpha Status)**

   This module is actively under development and is intended primarily for
   **Glo deployments** while we refine feature stability.

   As with any early-stage feature, functionality may evolve.

   That said, this module is the intended replacement for our ``connector_edi`` suite
   of modules and offers a vast simplification - we do not anticipate its removal.

   However, Glo stands fully behind our customers: should this module change direction
   or be phased out, Glo will work with you on a migration path.

The **sale-EDI-ish engine** for `autopilot` connectors: the common
import-order / acknowledge / dispatch-note (ASN) / invoice workflow, factored
out so a trading partner is a thin *dialect* rather than a whole module.

It is a bespoke connector's shared mechanism, not a configurable engine. All of
sweeping/claiming files, creating orders + bindings, binding eligible
pickings/invoices, queueing per-record delivery jobs and the transport live
here, in code; the only per-partner part is the **format**, and that is a set of
convention-named methods a bridge adds.

When to use it (and when not)
=============================

Use ``autopilot_sale`` when a trading partner **exchanges sale documents as
files** - they drop order files and expect acknowledgement / dispatch-note /
invoice files back, in **their own format**, over a file transport
(SFTP/S3/local) - and the process is Odoo's ordinary **order -> delivery ->
invoice** lifecycle. That shape (one partner, batch file exchange, one-directional
lifecycle documents, a format that differs per partner and changes occasionally,
no live external system to keep in sync) is common enough - YPO, and most
B2B/public-sector EDI feeds - that the ~95% of plumbing identical between partners
is not worth rebuilding. A new partner is then just a *dialect*: a handful of
parse/render methods.

Use ``autopilot_sale`` when you have many of the same basic shape. For unique one off
connectors, it may be worth while avoiding ``autopilot_sale``.

Do **not** stretch it to cover a live, bidirectional platform integration -
Magento, Shopify, a marketplace. Those are a different animal: high volume, many
record types (catalog, stock, price, customers, orders), webhook/real-time,
stateful two-way sync needing durable external-id bindings. There is no file to
sweep and no single lifecycle to ride, so forcing them through a file-dialect
distorts both - they belong in a dedicated API connector, not here.
Also out of scope: 3PL / warehouse dispatch and anything that is not the sale
lifecycle.

Rule of thumb: **files + a partner's format + the sale lifecycle -> a dialect here;
a live API + continuous two-way sync -> its own connector.**

Dialects (the registry is a naming convention)
==============================================

``autopilot_sale.backend.dialect`` is a ``Selection`` a bridge extends with
``selection_add``. The engine's crons then delegate to methods named
``_<dialect>_<verb>`` that the bridge adds by ``_inherit`` — that method-name
convention *is* the whole registry:

* ``_<dialect>_import_orders(path)`` — the import cron **claims each inbound file
  and hands it to this method as its own queued job**. The dialect reads/parses
  that one file and creates the ``sale.order`` + ``autopilot_sale.order`` (+
  ``.line``) bindings itself; the engine does none of it. Make it idempotent
  (reuse a reference already bound) so a retried job is safe.
* ``_<dialect>_export_acks(order_bindings)`` — acknowledgement **rides the
  import**: the dialect calls its own ack from within ``import_orders``. It is
  not a cron; its mere existence lights up the acknowledgement transport page.
* ``_<dialect>_export_asns()`` / ``_<dialect>_export_invoices()`` — their own
  crons delegate here. The dialect finds the eligible pickings/invoices, renders,
  ``_place``\ s the file, and records a binding (whose existence is the
  "already sent" marker). Queue per record inside if you want retry isolation.
