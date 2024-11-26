-------------------
concurrency_warning
-------------------

When a user is viewing a record within the Odoo backend web UI, and the record
is changed, when configured the system will notify the user that the record has
changed and reload the record.

Additional configuration is required per-model to enable this feature. This is
by design to ensure that we do not effectively spam the user about records they
do not care about.

Example usage
--------------

::

    <record id="poke_sale_order_on_write" model="base.automation">
      <field name="name">Poke on Sale Order Change</field>
      <field name="model_id" ref="sale.model_sale_order"/>
      <field name="state">poke</field>
      <field name="trigger">on_write</field>
    </record>

    <record id="poke_purchase_order_on_write" model="base.automation">
      <field name="name">Poke on Purchase Order Change</field>
      <field name="model_id" ref="purchase.model_purchase_order"/>
      <field name="state">poke</field>
      <field name="trigger">on_write</field>
    </record>

