===================
account_tax_plastic
===================

⚠️This is a convenience module only. Further configuration is required.


Extends ``account_tax_python`` to support weight-based plastic taxes for
businesses shipping into EU member states.

Adds a ``Plastic Weight`` field (in the system weight unit) to
``product.template``, and provides a pre-configured formula-based tax record::

    product.plastic_weight * quantity * <RATE PER KG>

Weights are converted to kg before the tax is calculated, so rates are always
per kg, even if the system weight unit is lb.

Configuration
-------------

1. Set the correct rate in the formula (Accounting -> Configuration -> Taxes ->
   *Plastic Tax*). Duplicate the record for countries with different rates.

2. Set ``Plastic Weight`` on each applicable product.

3. Apply the tax(es) to the appropriate fiscal positions so they are triggered
   automatically by the customer's country.

Shipment Plastic Tax
--------------------

Some documents charge plastic tax on a whole shipment rather than per product.
Set this up under Accounting -> Configuration -> Settings -> Taxes -> *Plastic Tax*:

* **Basis**: whether the shipment's net or gross weight is charged.
* **Rate per kg**: the amount per kg, and its currency (EUR by default).

Modules then call ``res.company._get_plastic_tax(net_weight, gross_weight,
currency, date)`` for the amount, converted into the document's currency.
