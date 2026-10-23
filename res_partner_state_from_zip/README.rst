res_partner_state_from_zip
==========================

Fills a contact's blank state from its zip.

Rules live under Contacts > Configuration > Localization > Zip Prefixes. Each
maps a zip prefix to a state. The longest match wins, so ``B`` and ``B1`` can
point to different states.

It runs when a contact is created, or its zip or country changes. To backfill,
select contacts and run "Fill State from Zip".

It never overwrites a state. A state cleared by hand stays blank until the zip
or country changes.

Contacts without a country are skipped. Set the system parameter
``res_partner_state_from_zip.fallback_company_country`` to ``True`` to use the
company's country instead.

Limitations
-----------

* Only GB rules are shipped. They use historic postal counties, so Manchester
  is Lancashire and Bristol is Avon.
* GB districts split across counties (CV8, GU17, IP21, NP7, RH6, TD12, TN2) use
  the county of their main post town.
* GB rules are generated from Wikipedia's "List of postcode districts in the
  United Kingdom" (CC BY-SA 4.0). They load ``noupdate``, so local edits
  survive upgrades, but fixes upstream won't arrive.
