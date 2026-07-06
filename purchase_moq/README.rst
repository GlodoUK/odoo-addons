============
purchase_moq
============

Per-supplierinfo minimum order quantities (MOQ).

Suppliers often refuse to fulfil a purchase order line below a given
quantity. This module lets you record that threshold against each vendor
pricelist line (``product.supplierinfo``) and blocks confirmation of any
purchase order that falls short of it.

Configuration
=============

On a product's *Purchase* tab, each vendor line gains a **Minimum Order
Quantity** (``moq``) field, shown next to the standard *Quantity*
(``min_qty``) column. It defaults to ``0``, which means "no minimum".

The MOQ is always expressed in the **vendor line's unit of measure**, not
the product's default unit.

How it works
============

The check runs on ``purchase.order.button_confirm`` and only inspects
orders still in the ``draft`` or ``sent`` state. For each order line the
module:

1. Skips the line if it has no product or a zero quantity.
2. Skips the whole order if **Override MOQ** (``force_moq``) is ticked.
3. Resolves the relevant vendor line for the ordered product (see
   *Seller resolution* below).
4. Skips the line if that vendor line has no MOQ set (``moq == 0``).
5. Converts the ordered quantity into the vendor line's unit of measure
   and, if it is below the MOQ, raises a ``ValidationError`` naming the
   product, vendor and required minimum. The order stays in draft.

Ticking **Override MOQ** on the purchase order (under *Other Information*)
bypasses the check for that order entirely, allowing a sub-MOQ order to be
confirmed when a buyer has agreed an exception with the supplier.
