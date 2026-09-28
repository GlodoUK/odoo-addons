========================
product_alternative_sale
========================

Adds a popup widget to the sale order line that lists a product's alternatives and
opens the product catalog restricted to them.

Known limitation (dynamic variants)
------------------------------------
The sale catalog and the line widget both operate on ``product.product``
(materialised variants). Alternatives that resolve to a **dynamic** template
with no materialised variants will therefore not appear, and a new dynamic
configuration cannot be created from here - that requires the product
configurator, which is intentionally out of scope.

Dynamic alternatives only surface their already-materialised variants.

