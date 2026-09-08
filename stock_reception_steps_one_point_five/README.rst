==============================
stock_reception_one_point_five
==============================

Adds two "store manually" reception modes to warehouses.

**Receive then Store manually (1.5 steps)**

Goods are received into the Input location (the landing area) exactly like a
two-step receipt, but no automatic store move to Stock is generated. Operators
move stock from Input to Stock manually using the Storage operation type.

**Receive, Quality Control, then Store manually (2.5 steps)**

Goods are received into Input and automatically routed on to Quality Control
exactly like a three-step receipt, but no automatic store move to Stock is
generated. Operators move stock from Quality Control to Stock manually using
the Storage operation type.

Modelling these as first-class ``reception_steps`` values means the receipt
route, rules and operation types are regenerated correctly whenever the
warehouse is edited, instead of being clobbered by Odoo's standard machinery.

⚠️This should be carefully tested in your own environment.
There is a risk of other routes not working as expected depending on the configuration.
