==================
web_list_min_width
==================

Allows the attribute `min-width` to be set and enforced on a list / tree view.

Usage
=====

Set an attribute called `min-width` on a field with an appropriate unit::

  <xpath expr="//field[@name='order_line']/tree/field[@name='product_id']" position="attributes">
    <attribute name="min-width">10em</xpath>
  </xpath>


