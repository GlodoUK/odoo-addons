=======
cpq_mrp
=======

Configurable / BoMs on-demand.

- Adds a new "Configurable BoM" that generates kits and manufacturing orders on-demand
- Each component may be either a template or a variant.
  - A template will take compatible attributes from the parent item
  - A variant will work as per-standard Odoo
- Each component quantity may be dynamic
- More flexible filters for component usage
  - Always
  - Domain filters
  - "Apply on Variants" (as per standard Odoo)
- Nested BoMs are supported.

Usage
=====

Scenario: network cable (variants)
----------------------------------

- Imagine selling a network cable.
- You purchase a reel of 1000m of network cable at a time.
- You terminate the ends yourself in a manufacturing order
- You sell common sizes, 50cm, 100cm, 200cm, etc.
- You allow a customer to stipulate a custom length.

Setup:

- Create a Product Template for your unterminated network cable as per normal, ensure that it's UoM is cm and that you have a supplier.
- Create a Product Template for your manufactured network cable, which is Configurable = True
- Create a Product Template for the RJ45 ends, UoM = units
   - Add an attribute with values 50cm, 100cm, 200cm, and custom
   - Ensure that the custom attribute is set to `is_custom = True` and the `cpq_custom_type = float or integer`
- Create a Dynamic BoM through the Manufacturing app
   - The created product is your manufactured network cable
   - Ensure it is set to manufacture
   - Add 4 BoM lines:
      - Component Type: Variant, Variant: Unterminated network cable, Quantity Type: Fixed, Quantity: 50cm, Condition Type: Apply on Variants, select 50cm variant option
      - Component Type: Variant, Variant: Unterminated network cable, Quantity Type: Fixed, Quantity: 100cm, Condition Type: Apply on Variants, select 100cm variant option
      - Component Type: Variant, Variant: Unterminated network cable, Quantity Type: From Configurable Custom Value, Quantity: select Custom attribute, Condition Type: Apply on Variants, select custom variant
      - Component Type: Variant, Variant: RJ45 ends, Quantity Type: Fixed, Quantity: 2, Condition Type: Always

Scenario: Desk
--------------

TODO
