===============
Mail Autofollow
===============

Subscribe followers to records automatically, from a rule: pick a model, narrow
it down with a domain, list the contacts that should follow the matching
records.

Followers are added **as the record is created** - not when a mail template is
sent, not on a queued job. There is no menu to visit and no automation rule to
maintain.

Configuration
=============

*Discuss > Configuration > Auto Follow Rules*, or the same list under
*Settings > Technical > Email*. Both need the *Auto Follow Rules / Manager*
privilege; the Discuss one is the entry point for a manager who is not an
administrator, since the Technical menu itself is administrator-only.

Why not...
==========

* ``base_automation`` - whilst this can be achieved with base automation it requires
  administrator level access and cannot be accessed by lower permission users.
* Various OCA modules - honestly, we found that they work slightly differently and for
  most of our needs, not quite as we'd like. But they are great modules.

Escape hatch
============

Code that must create or update records without triggering the rules can pass
``mail_autofollow_skip=True`` in the context.
