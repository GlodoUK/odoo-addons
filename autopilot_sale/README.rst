==============
autopilot_sale
==============

.. caution::
   **Early Access (Alpha Status)**

   This module is under active development, mainly for **Glo deployments**,
   so it may still change.

   It replaces our ``connector_edi`` suite and is far simpler. We don't expect
   to remove it. If it does change direction, Glo will help you migrate.

Sale EDI for trading partners who send orders as files. Their orders arrive
in their own format, become ordinary Odoo sale orders, and the
acknowledgements, dispatch notes and invoices go back in that same format.
No retyping, and the partner gets their documents on time.

Each partner is a small **dialect**: a few methods that read and write their
format. Everything else is shared: picking up files, queuing, retries,
confirmation, sending, housekeeping.

When to use it
==============

Use it when a partner exchanges sale documents as **files** (SFTP, S3, a local
folder, or by email) in **their own format**, and the work follows Odoo's
normal order, delivery and invoice. Public sector buyers like YPO, and most
B2B feeds, look like this. Once you have a few, the shared plumbing pays for
itself.

Don't use it for a live platform integration such as Magento, Shopify or a
marketplace. Those sync many kinds of record both ways in real time, and need
their own connector. A one-off partner may also be simpler as its own module.

Rule of thumb: files in a partner's format along the sale lifecycle belong
here. A live API with two-way sync does not.

Setting up
==========

Under **Integrations & Connections > Sale EDI**, create a backend:

* **Dialect**: the partner's format.
* **Customer**: the default partner orders are placed against.
* **Connection**: a shared connection (SFTP and so on). Leave it empty for a
  partner who emails their files; managers can then use **Upload File**.
* **Paths**: where to pick orders up, where to move them once claimed, and
  where each outgoing document goes. Paths take ``{datetime:%Y}`` style
  tokens, and outgoing ones also take ``{record.name}`` style tokens.
* **Confirmation**: see below.
* **Access Groups** (optional): limit the backend and its records to these
  groups. **Notified Users** follow it, so they hear about errors.

How it works
============

**Orders.** Every 15 minutes the backend moves new files from the source
folder into the processed folder. Moving a file is how it is claimed, so it
is never read twice. Each file becomes an order file record, queued as a job.

That job only *stages*: the dialect splits the file into one order record per
order, with its rows kept as ``payload``. Each order is then its own job,
which creates the sale order, confirms it and queues the acknowledgement. So
one bad order fails alone, and a retry does not re-read the file.

Files and orders keep their own state (pending, done, failed, cancelled) and
error, where a sales user can see them. **Retry** queues one again; **Cancel**
stops a queued one. A failed order is rolled back cleanly.

**Confirmation** policies:

* **Leave as Quotation** (default).
* **Confirm, Fail on Error**: if Odoo refuses to confirm, the order fails and
  nothing is kept. Fix the cause and retry.
* **Confirm, Keep Quotation on Error**: if refused, the quotation stays, with
  the reason posted on it and on the backend.

The acknowledgement is queued inside the order's own job, so an order that
rolls back never sends one.

**Dispatch notes and invoices.** Every 15 minutes the backend finds done
customer deliveries and posted invoices for its orders, and queues each one
to be sent. A record is only ever sent once.

**Seeing what happened.** A sale order that came in by EDI has an **EDI**
button showing whether it was received. Files, orders, dispatch notes and
invoices all appear in **Integrations & Connections > Activity**, next to
every other connector, so failures are easy to spot.

Writing a dialect
=================

A dialect is a bridge module. It adds a ``dialect`` value and methods named
after it; that naming convention is the whole registry:

.. code-block:: python

    class AutopilotSaleBackend(models.Model):
        _inherit = "autopilot_sale.backend"

        dialect = fields.Selection(
            selection_add=[("acme", "Acme")], ondelete={"acme": "cascade"}
        )

        def _acme_compute_supports_import_order(self):
            return True

        def _acme_import_order(self, file):
            Order = self.env["autopilot_sale.order"]
            with file._open() as handle:
                rows = etl.csv.read_rows(handle)
            for ref, order_rows in group_by_ref(rows):
                Order.create(
                    {
                        "backend_id": self.id,
                        "external_ref": ref,
                        "payload": Order._encode_payload(order_rows),
                    }
                )

The methods:

* ``_<dialect>_compute_supports_<flow>()`` turns a flow on. The flows are
  ``import_order``, ``ack``, ``asn`` and ``invoice``. Without it, a flow is off.
* ``backend._<dialect>_import_order(file)`` stages one order record per order.
  Skip references already staged, so a re-sent file is safe.
* ``autopilot_sale.order._<dialect>_create_order()`` builds the sale order
  from ``_read_payload()``.
* ``autopilot_sale.order._<dialect>_acknowledge()``,
  ``autopilot_sale.picking._<dialect>_export()`` and
  ``autopilot_sale.invoice._<dialect>_export()`` render a document and write
  it with ``backend._place(path, record=...)``.

Partner references with no column of their own go in ``external_values``.

Job channels
============

Each flow has its own job channel field on the backend: **Orders**,
**Acknowledgements**, **Dispatch Notes** and **Invoices**, so imports can be
preferred over sending. Empty means queue_job's ``root``. An unconfigured
channel runs under its nearest configured parent.

Keep the orders channel at capacity 1: orders find or create delivery
addresses, and parallel jobs would race. For example::

    channels = root:1,root.edi.orders:1,root.edi.acks:1

Housekeeping
============

A daily job clears the stored file and each order's payload once done and
older than the backend's **Keep For** period (30 days by default). Anything
not done keeps its copy, ready for a retry.
