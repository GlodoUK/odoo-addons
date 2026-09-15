========================
res_partner_ref_sequence
========================

Assign a company's partner reference from a sequence chosen by rule.

Usage
=====

Configure the rules under *Contacts > Configuration > Reference Rules*. A rule is
a domain over ``res.partner`` and the ``ir.sequence`` to draw from; rules are
evaluated in order and the first whose domain matches the partner wins, so put
the narrow rules first and keep a catch-all (an empty domain) last. The module
ships one such catch-all, ``Default``, using the *Partner Reference* sequence.

On the contact form, a **Generate** button sits next to *Reference* on the
*Sales & Purchase* tab. It appears only for companies with no reference yet, and
takes the next number from the first matching rule's sequence.

Why not the OCA modules?
========================

OCA's ``partner_sequence`` (and friends) assign the reference automatically on
create, from one sequence for every partner. That is the right answer when the
reference is just an internal counter and nobody should have to think about it.

This module takes the opposite position on both points:

* **Manual, not automatic.** The reference is only allocated when someone
  presses **Generate**. Partners created by imports, website signups, EDI or the
  portal do not silently burn sequence numbers, and a contact can exist for a
  while before it is worth giving it a customer number at all.
* **Several sequences, not one.** Which sequence is used is decided by rule, so
  different kinds of partner can carry visibly different references — per
  country, per company, per commercial segment, whatever the domains say —
  instead of everyone sharing a single run of numbers.

If you want hands-off numbering with a single series, use the OCA module; it is
simpler and does that job well.
