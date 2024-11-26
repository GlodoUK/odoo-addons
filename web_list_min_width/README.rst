==================
web_list_min_width
==================

- Adds a min-width field option to force a minimum width on a field
- Adds an 'initial-width' field option to force initial width on a field

Usage
=====

Set an option called `min-width` on a field with an appropriate unit::

  <xpath expr="//field[@name='order_line']/tree/field[@name='product_id']" position="attributes">
    <attribute name="options">{'min-width': '12rem'}</xpath>
  </xpath>


Set an option called `initial-width` on a field with an appropriate unit::

  <xpath expr="//field[@name='order_line']/tree/field[@name='product_id']" position="attributes">
    <attribute name="options">{'initial-width': '16rem'}</xpath>
  </xpath>


Deprecated
----------

For backwards compatibility an attribute called "min-width" is supported,
however this is non-functional on fields outside of forms. The options approach
is recommended going forward.

Set an attribute called `min-width` on a field with an appropriate unit::

  <xpath expr="//field[@name='order_line']/tree/field[@name='product_id']" position="attributes">
    <attribute name="min-width">10em</xpath>
  </xpath>

