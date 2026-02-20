============================
stock_barcode_putaway_rules
============================

Add a button to the barcode app that allows users to manually trigger putaway
rule evaluation on a picking's move lines.

- Adds a **Show 'Apply Putaway Rules' in Barcode** boolean on the picking type
  form, controlling whether the button appears.
- When the feature is enabled, an **Update Storage Location** button is shown
  in the barcode app for pickings of that type.
- Clicking the button calls ``_apply_putaway_strategy`` on the picking's move
  lines, re-evaluating putaway rules and updating destination locations
  accordingly.

Usage
=====

Enabling the Feature
--------------------

1. Navigate to the picking type form (Inventory > Configuration > Operation
   Types).
2. Tick the **Show 'Apply Putaway Rules' in Barcode** checkbox.

Using the Button
----------------

1. Open a picking of the enabled type in the barcode app.
2. Click the **Update Storage Location** button in the control bar.
3. The putaway rules are evaluated against the current move lines and
   destination locations are updated.
