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

It is a bespoke connector's shared mechanism, not a configurable engine. The
connection, claiming and uploading files, the per-file and per-order jobs and
their states, confirmation, binding eligible pickings/invoices, job channels
and housekeeping live here, in code; the only per-partner part is the
**format**, and that is a set of convention-named methods a bridge adds.

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
``selection_add``. The engine then delegates to methods named
``_<dialect>_<verb>`` that the bridge adds by ``_inherit``, and offers each flow
only when ``_<dialect>_compute_supports_<flow>`` says so — that method-name
convention *is* the whole registry:

* ``_<dialect>_import_order(file)`` - an ``autopilot_sale.order.file`` arrives
  either from the import cron, which **claims each inbound file** off the
  connection, or from **Upload File** on the backend (managers; no connection
  needed - for a partner who emails their files). Either way its bytes are kept
  on the record (``data``, an attachment) and the file is queued as its own
  job. The dialect reads it with ``file._open()`` - it never cares where the
  file came from - and **stages** one ``autopilot_sale.order`` per order -
  ``external_ref`` plus the order's rows in ``payload`` - and nothing else.
  Skip references already bound so a retried or re-uploaded file is safe. The
  file is done once its orders are staged.

* ``autopilot_sale.order._<dialect>_create_order()`` — the engine then queues
  **each staged order as its own job**. The job runs
  ``_process``: the dialect builds the ``sale.order`` (+ ``.line`` bindings)
  from ``_read_payload()``; the engine confirms it per the backend's
  **Confirmation** policy (``_confirm``); then, if the dialect acknowledges,
  queues ``_acknowledge`` (the dialect's ``_<dialect>_acknowledge()``) as its
  own job on the acknowledgement channel. It is queued inside the order's
  transaction, so an ack is never sent for an order whose job rolls back; a
  backend with no connection (upload only) sends none.

  Files and orders keep their own ``state`` (pending / done / failed /
  cancelled) and error, written by their job (``autopilot_sale.job.mixin``):
  the work runs in a savepoint, and a failure is recorded on the record
  rather than left only in the technical Job Queue. **Retry** queues it again;
  **Cancel** marks it so a still-queued job does nothing. Concurrency errors
  are left to queue_job's own retry. So one bad order fails and is retried
  alone.
  **Housekeeping** on the backend (on by default, 30 days): a daily cron
  (``_cron_cleanup``, for every backend that has it on, archived ones too)
  clears each file's stored copy once its import is done, and each order's
  payload once the order is done, when older than the period. Pending,
  failed and cancelled ones keep theirs for a retry.

  The backend's **Tracking** (UTM campaign, source, medium) is copied onto each
  new sale order wherever the dialect left it empty.

  Confirmation policies: **Leave as Quotation** (default); **Confirm, Fail on
  Error** - a refused confirmation fails the order and rolls it back;
  **Confirm, Keep Quotation on Error** - the confirmation runs in a savepoint,
  and a refusal leaves the quotation with the reason posted on it and on the
  backend. Only business refusals (``UserError``/``RedirectWarning``, or
  ``action_confirm`` returning without confirming) are recovered.
* ``autopilot_sale.picking._<dialect>_export()`` /
  ``autopilot_sale.invoice._<dialect>_export()`` — the dispatch-note and invoice
  crons find the eligible pickings/invoices themselves, bind each (the
  binding's existence is the "already sent" marker) and queue its export; the
  dialect renders and ``_place``\ s the file.

Job channels
============

Every Sale EDI job is queued through ``backend._delay(records, channel)``, with
one channel field per operation on the backend: **Orders** (the file job and
each order's job), **Acknowledgements**, **Dispatch Notes** and **Invoices** -
so, say, importing orders can be preferred over sending acks. An empty field
passes no channel (queue_job's default, ``root``). A channel that is not in
the queue_job ``channels`` config runs under its nearest configured parent, so
set capacities there, keeping the orders channel at capacity 1 (a file's
orders find-or-create addresses and would race), e.g.
``channels = root:1,root.edi.orders:1,root.edi.acks:1``.
