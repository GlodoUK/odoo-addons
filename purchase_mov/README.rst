============
purchase_mov
============

Per-vendor minimum order values (MOV).

Suppliers often refuse to fulfil a purchase order below a given monetary
value. This module lets you record that threshold against the vendor and
blocks confirmation of any purchase order that falls short of it.

Configuration
=============

On a partner's *Sales & Purchase* tab, the *Purchase* group gains a
**Minimum Order Value** (``property_purchase_mov``) field. It defaults to
``0``, which means "no minimum".

The field is ``company_dependent``, so each company records its own
threshold for the same vendor.

Currency
========

The MOV is expressed in the vendor's **Supplier Currency**
(``property_purchase_currency_id``, itself already ``company_dependent`` in
core ``purchase``), falling back to the **company currency** when the vendor
has none.

Known limitations
=================

* The MOV is read off ``order.partner_id`` directly, matching how core reads
  ``property_purchase_currency_id``. A threshold set on a parent company is
  *not* inherited by its child contacts.
* The comparison uses ``amount_untaxed``; taxes and delivery charges added as
  taxes do not count towards the minimum.
