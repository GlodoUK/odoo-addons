Report Layout No Header No Footer
=================================

Conditionally hide the header and/or footer in report layouts

Supports all standard report layouts defined in `odoo/addons/web/data/report_layout.xml`

- Bold
- Boxed
- Light
- Striped

Example usage:

.. code-block:: xml

<t t-call="web.external_layout">
    <t t-set="no_header" t-value="True" />
    <t t-set="no_footer" t-value="True" />
</t>

.. code-block:: xml

<xpath expr="//t[@t-call='web.external_layout']" position="inside">
    <t t-set="no_header" t-value="True" />
    <t t-set="no_footer" t-value="True" />
<xpath>
