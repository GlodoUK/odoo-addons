========================
sale_mrp_phantom_explode
========================

Optionally explode a kit into its component parts on a sale order, rather than
waiting for the confirmation of a sale.

Kit lines on a draft/sent order get an "Explode kit into components" button.
Pressing it saves the order and replaces the kit line, in place, by a section
named after the kit followed by one line per storable component.

For background / programmatic order entry,
``sale.order.line.action_sale_mrp_phantom_explode()`` does the same and works
like ``stock.move.action_explode()``. Non-kit lines are left untouched.

Sections own every line below them up to the next section, so lines that sat
below the kit line end up under the kit's section.

This is a lighter/alternative to:

- Combos
- OCA Packs
- OCA Sets

Which builds on top of standard MRP phantom/kits.
