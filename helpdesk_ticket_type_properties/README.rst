Helpdesk Ticket Type Properties
===============================

Adds a Properties field ``ticket_type_properties`` to ``helpdesk.ticket``
These properties are displayed on the helpdesk ticket portal view

Historically named ``helpdesk_ticket_type_properties`` due to the now-removed ``ticket_type_id`` field on helpdesk tickets.
In 18.0 this was been replaced by ``ticket_categ_id`` from our ``helpdesk_ticket_category`` module.

Known issues:

    - Suffixes not shown on the portal view for Multiline Text properties
    - It would be nice to visualise Tags and Many2many properties on the portal view as many2many_tags rather than concatenated strings
