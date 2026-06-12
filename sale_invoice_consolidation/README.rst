==========================
sale_invoice_consolidation
==========================

Per-customer control over how and when sale orders are invoiced, both automatically and
manually.

Adds an invoice consolidation preference and an optional automatic invoicing schedule
to each customer.

Consolidation preference
-------------------------

A customer (``res.partner``) can be set to one of:

* **Consolidated** - all of the customer's invoiceable orders are merged into a
  single invoice per ``_get_invoice_grouping_keys`` (company, partner, shipping
  address, currency, fiscal position).
* **Individual** - one invoice per sale order.

The preference overrides the ``grouped`` argument on
``sale.order._create_invoices``, so it applies whether invoices are raised from
the *Create Invoice* wizard or automatically. Orders whose invoicing partner has
no preference fall back to the caller's choice.

Automatic invoicing
-------------------

Each customer can be given an **Auto-Invoice Frequency** (daily, weekly, monthly,
quarterly) and a **Next Auto-Invoice Date**. A daily scheduled action invoices
the pending orders of any customer whose next date has arrived, then rolls the
date forward.

* The next date advances by whole periods from the
  previous date, so the cadence stays anchored (a customer billed monthly on the
  1st stays on the 1st) and missed runs are caught up in a single jump rather
  than invoiced one period per run.
* Progress is reported through ``ir.cron._commit_progress``: each
  customer is committed as it completes, so a timed-out run resumes where it left
  off, and a failure rolls back only the customer being processed.
* A note is logged on the customer recording how many invoices
  were automatically raised.

All scheduling and consolidation fields are ``company_dependent``, so values can
differ per company.

Configuration
-------------

Set the preference, frequency and next date on the *Invoicing* tab of the
partner used as the order's invoice address. This may be a company or one of its
child contacts - the settings are read from the invoice address itself and are
not inherited from the commercial entity, so configure them on the partner you
actually invoice. Leaving the frequency empty disables automatic invoicing for
that partner.
