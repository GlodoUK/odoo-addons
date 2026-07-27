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

Each customer can be given an **Auto-Invoice Frequency** (hourly, daily, weekly,
monthly, quarterly) and a **Next Auto-Invoice Run**. A scheduled action invoices
the pending orders of any customer whose next run is due, then rolls the moment
forward.

* The next run advances by whole periods from the
  previous value, so the cadence stays anchored (a customer billed monthly on the
  1st stays on the 1st) and missed runs are caught up in a single jump rather
  than invoiced one period per run.
* ``Next Auto-Invoice Run`` is a datetime, stored and compared in UTC, so sub-day
  cadences are possible. The **hourly** cadence only fires as often as the
  scheduled action runs - the action ships at a 1-hour interval. Coarser
  cadences (daily and up) are unaffected by how often the action runs, because
  each customer is gated on their own next-run moment.
* Progress is reported through ``ir.cron._commit_progress``: each
  customer is committed as it completes, so a timed-out run resumes where it left
  off, and a failure rolls back only the customer being processed.
* A note is logged on the customer recording how many invoices
  were automatically raised.

All scheduling and consolidation fields are ``company_dependent``, so values can
differ per company.

Sale orders carry a read-only **Automatic Invoicing** mirror
(``sale.order.sale_auto_invoice_enabled``), shown on the *Other Info* tab, so it
is visible from the order whether the scheduled action will pick it up. It is
computed from the **Auto-Invoice Frequency** of the order's invoice address, read
in the order's company.

Automatic credit notes
----------------------

Each company has an **Auto-Raise Credit Notes** setting
(``res.company.sale_auto_invoice_credit_notes``, on by default) that decides
whether the scheduled action invoices with Odoo's ``final`` flag.

* **On** - pending negative quantities (returns, downward corrections after
  invoicing) are picked up and the resulting negative invoice is switched to a
  credit note.
* **Off** - only positive quantities are invoiced automatically. Orders whose
  only pending quantity is negative are left alone for someone to credit by
  hand; they do not hold up the customer's schedule, which still rolls forward.

Only the scheduled action is affected. Manual invoicing from the *Create
Invoice* wizard keeps Odoo's own behaviour, where ``final`` follows the wizard's
*Deduct down payments* option.

Configuration
-------------

Set **Auto-Raise Credit Notes** in *Accounting > Configuration > Settings*,
under *Consolidation*.

Set the preference, frequency and next run on the *Invoicing* tab of the
partner used as the order's invoice address. This may be a company or one of its
child contacts - the settings are read from the invoice address itself and are
not inherited from the commercial entity, so configure them on the partner you
actually invoice. Leaving the frequency empty disables automatic invoicing for
that partner.
