============================
stock_putaway_classification
============================

Put-away by product value/volume classification (e.g. Netstock's "High Value,
High Volume"), keeping one pick face per product.

* ``product.classification`` records (Inventory > Configuration > Product
  Classifications), each with a ``code`` for integrations. None are shipped;
  the database's own bootstrap creates them.
* ``product_classification_id`` on the product (variant, mirrored on
  single-variant templates) and on put-away rules.
* A rule with a classification only applies to products with that
  classification, and ranks after product and category rules but ahead of
  catch-alls.
* A classification rule is skipped while the product already has stock in,
  or on its way to, the rule's *Store to* location. Pair it with a storage
  category set to "If location is empty": a product gets an empty pick face
  when it has none, otherwise put-away falls through to the next rule (bulk).
* Storage categories set to "If location is empty" also refuse locations with
  stock already on its way in (core only checks stock on hand).
* Storage categories with *Only Listed Package Types* refuse packages of a
  type they have no capacity line for (core only limits the listed types).
  Unpackaged stock is unaffected.
* Classifications display as ``[code] name`` and can be searched by code.

Typical layout, one storage category per classification and load size::

    WH/Stock/Pick/<bin>   "High Value, High Volume: Euro Pallet 1.6M", ...
    WH/Stock/Bulk/<bin>   "Bulk: Euro Pallet 1.6M", ...

Each category takes one package of its own type, only while empty. Put-away
rules on ``WH/Stock`` (receipts) and ``WH/Stock/Pick`` (replenishment) send
each classification to its categories under ``WH/Stock/Pick``, one rule for
the package type and one for unpackaged stock, and ``WH/Stock`` falls back to
the ``WH/Stock/Bulk`` categories. A min/max rule on ``WH/Stock/Pick`` with a
Bulk -> Pick route refills a product's pick face once it runs out; the
classification rules pick the face.
