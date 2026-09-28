=========================
res_partner_activity_feed
=========================

HubSpot-style activity feed on the partner form, built on ``mail.message``.

Adds an "Activity Feed" action to the contact form which shows a single
chronological timeline of emails, notes and document lifecycle events
(orders sent/confirmed, invoices validated/paid, leads won/lost, ...) for
a partner. The feed always operates at the commercial partner level and
rolls up messages from all child contacts and their documents.

Common document models (CRM leads, sale/purchase orders, invoices,
pickings, helpdesk tickets) are included speculatively — none of them are
dependencies; models missing from the registry are simply skipped.
Machine chatter (field tracking, automated log notes, per-user
notifications, blank bodies) is filtered out.

Extending
=========

To pull another model into the feed, extend
``FEED_DOCUMENT_MODELS``/``FEED_EVENT_SUBTYPES`` or override
``res.partner._activity_feed_domains()``. Card icons and amount summaries
are configured in ``FEED_ICONS`` and ``FEED_SUMMARIES`` on
``mail.message``.
