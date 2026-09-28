===================
account_tax_plastic
===================

⚠️This is a convenience module only. Further configuration is required.


Extends ``account_tax_python`` to support weight-based plastic taxes for
businesses shipping into EU member states.

Adds a ``Plastic Weight`` field (in the system weight unit) to
``product.template``, and provides a pre-configured formula-based tax record::

    product.plastic_weight * quantity * <RATE>

Configuration
-------------

1. Set the correct rate in the formula (Accounting -> Configuration -> Taxes ->
   *Plastic Tax*). Duplicate the record for countries with different rates.

2. Set ``Plastic Weight`` on each applicable product.

3. Apply the tax(es) to the appropriate fiscal positions so they are triggered
   automatically by the customer's country.
