==================
autopilot_purchase
==================

Sends your confirmed purchase orders to a vendor as files, in the vendor's own
format. No more retyping orders into a portal or emailing spreadsheets. Confirm
the order in Odoo and it goes.

It only sends. Acknowledgements, receipts and invoices don't come back this way.

The shared work lives here: knowing which orders to send, when, where, and what
happened. Each vendor's format is a small *dialect* module, such as
``autopilot_purchase_cosy_ypo``. It is the purchase sibling of
``autopilot_sale``.

Setting up
==========

Under **Integrations & Connections > Purchase EDI**, create a backend and set:

* **Dialect**: the vendor's format.
* **Vendor**: orders to this partner, or any of its contacts, are sent.
* **Connection**: where files go. Leave it empty to pause sending.
* **Orders Path**: the full file path. ``{record.*}`` is the order file and
  ``{datetime:...}`` the time, for example
  ``/out/orders/{record.purchase_order_ids[0].name}-{datetime:%Y%m%dT%H%M%S}.csv``.
  Keep it unique per file, or files overwrite each other.

How it works
============

1. **Confirm** a purchase order to the vendor. It is linked to the backend and
   shows **EDI: To Send** on its smart button straight away. Orders confirmed
   before the backend existed are never sent, so setting one up is safe.
2. **Every 15 minutes** the backend gathers its To Send orders into files and
   queues each file as its own job. An order cancelled in the meantime waits,
   and goes if it is confirmed again.
3. **Each job** builds the file through the dialect, writes it to the
   connection and keeps a copy. The order's chatter says it was sent.

An order is only ever sent once. If something goes wrong:

* **Retry** a failed file. It is rebuilt from the orders as they are now, so
  fix the order first and retry.
* **Cancel** a file you don't want sent.
* **Send Again** sends a fresh file, for when the vendor lost it or the order
  changed.

Failures show on the file, on the order's EDI button and in
**Integrations & Connections > Activity**.

Writing a dialect
=================

Add a ``dialect`` value and render the file::

    class AutopilotPurchaseBackend(models.Model):
        _inherit = "autopilot_purchase.backend"

        dialect = fields.Selection(
            selection_add=[("acme", "Acme")], ondelete={"acme": "cascade"}
        )

    class AutopilotPurchaseOrderFile(models.Model):
        _inherit = "autopilot_purchase.order.file"

        def _acme_render(self):
            # Return the file's bytes for self.purchase_order_ids.
            ...

Each file holds one order by default. To put several in one file, return the
groups from ``_acme_batch`` on the backend::

        def _acme_batch(self, bindings):
            return [bindings]  # everything found in a run, in one file
