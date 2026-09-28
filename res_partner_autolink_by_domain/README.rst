Partner Autolink by Email Domain
================================

When a contact is created from an incoming email, this module files it under the
contact that owns the sender's email domain. A mail from ``test@example.com``
creates ``test@example.com`` as a child of the ``Example`` contact, so it picks up
the right commercial partner instead of sitting loose at the top level.

Usage
-----

List the domains a customer is known by on their company contact, under the
**Email Domains** tab. A domain may only be listed against one contact — a domain
resolving to two contacts identifies neither.

Shared domains must never identify a customer. 200 webmail providers, ISPs,
disposable address services and common typos are shipped pre-banned, under
**Contacts > Configuration > Banned Autolink Email Domains**. Archive an entry
rather than deleting it, or the next upgrade of this module restores it.
