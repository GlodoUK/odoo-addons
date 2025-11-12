maintenance_request_template
----------------------------

Preventative maintenance requests can be recurring.

In 18.0 the ``description`` field is copied from the original maintenance request.

If you want to use the ``description`` field as a checklist, for example, then you don't want the checklist values to be propagated to new maintenance requests. This is an overkill module that provides a general framework to achieve this.

Priority 

``equipment_id.template_id.description``
``equipment_id.category_id.template_id.description``
``equipment_id.note``

``equipment_id.note`` is used for legacy data reasons
