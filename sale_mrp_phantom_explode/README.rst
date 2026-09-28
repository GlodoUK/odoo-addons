========================
sale_mrp_phantom_explode
========================

Optionally explode a kit into it's component parts on a sale order, rather than
waiting for the confirmation of a sale.

Each phantom/kit BoM has an "Explode on Sale Orders" mode:

- *(empty)*: never explode on sale orders (the default)
- *Ask*: when the kit is picked on a sale order line, offer to explode it via a
  dialog where the quantity can be adjusted
- *Always*: explode automatically when the kit is picked, with a notification

The exploded components are housed under a section line named after the kit.

For background / programmatic order entry,
``sale.order.line.action_sale_mrp_phantom_explode()`` works like
``stock.move.action_explode()``: it replaces any explodable kit lines with a
section line and their component lines, and returns the resulting lines. It ignores the
Ask/Always distinction - calling it is the consent - but lines whose BoM has no
explode mode set are left untouched.

This is a lighter/alternative to:

- Combos
- OCA Packs
- OCA Sets

Which builds on top of standard MRP phantom/kits.
