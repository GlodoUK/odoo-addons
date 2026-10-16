Stock Scrap Location
====================

Brings back the Scrap Location flag that Odoo removed in 19.0

(odoo/odoo#215517)

In 19.0 a new scrap goes to the company's Inventory Loss location with the lowest ID. 

This module allows a company to flag an Inventory Loss location as the scrap location, and new scraps will go there instead.
If a company has no flagged location, new scraps keep the default 19.0 behaviour.
