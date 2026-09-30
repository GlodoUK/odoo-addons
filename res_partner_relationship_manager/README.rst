res_partner_relationship_manager
=================================

Adds a commercial field ``relationship_manager_user_id`` to ``res.partner``

We use ``relationship_manager_user_id`` rather than ``user_id`` because ``user_id``
is tied to Odoo's built-in business logic (e.g. salesperson
assignment, lead routing, invoicing defaults). Reusing it would cause unintended
side effects across sales, CRM, and accounting workflows.
