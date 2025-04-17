-------------------
concurrency_warning
-------------------

When a user is viewing a record within the Odoo backend web UI, and the record
is changed, when configured the system will notify the user that the record has
changed and (optionally) reload the record.

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


Notes on the implementation
---------------------------

This module works on a broadcast system (limited to internal users).
Over the bus.bus websocket. This is obviously problematic for at least 2 reasons:

1. Potentially exposes (limited) information to users who should not see things
2. It's just wasteful

In an ideal world we would join and leave channels based on the currently viewed record.

In practice this leaves a few problems:

1. The bus doesn't actually differentiate the channel on the javascript side (when you
   subscribe to an event from the bus service). Meaning that you still need to verify
   the currently viewed record anyway!

2. If you attempt to join and leave channels (imagine 1 dynamic channel per record),
   when you rejoin you receive stale records from upto 50 seconds ago. Considering that
   the "pokes" are emphemeral this is problematic.

3. Hooking into FormController it's actually properly fiddly to know when you're viewing
   a new record and leaving. There's a lot of nuance (in at least 18) about when
   OnWillLoadRoot, OnWillUnmount, destroy, etc. are all called.
   We'd also need to duplicate this for other things like FormController.

Potential solutions:

1. Current implementation.

2. A lot of super'ing in the bus module to support completely emphermal messages.
   Practically this would be unwise as we'd need to completely replace several methods.

3. A new endpoint, like /websocket. Practically that would be problematic to run outside
   of certain hosting environments.

4. Allow all models to have their own channels. They need to placed onto an allow-list
   explicitly, meaning lots of glue modules, breaking backwards compatibility.

5. ??
