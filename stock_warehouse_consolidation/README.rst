=============================
Stock Warehouse Consolidation
=============================

Tracks how full each storage package is and helps operators consolidate stock
into fewer packages, and packages into fewer locations, to free up space.

What it does
============

* Adds a **capacity** notion to packages: how many units of a product fit on a
  single package of a given type, and therefore how full each package is right
  now.
* Provides two on-demand consolidation flows:

  * **Package consolidation** - merge the stock of several part-full packages of
    one product into a single package, emptying the others.
  * **Location consolidation** - move whole packages out of part-full locations
    into fewer locations, emptying the others.

* Both flows only ever **raise an internal transfer** for an operator to carry
  out; the module never moves stock itself.
* Both lists are computed **fresh each time they are opened** - nothing is
  stored, flagged or scheduled.

Configuration
=============

* Enable **Packages** and **Storage Locations** in *Inventory → Configuration →
  Settings*.
* Tick **Can be consolidated** on the package types to include
  (*Inventory → Configuration → Delivery → Package Types*). Everything below
  ignores any other package type.
* Define capacities in *Inventory → Configuration → Products → Package
  Capacities*: one row per product and package type, with the maximum quantity
  one package holds.
* For location consolidation, use **core storage categories**
  (*Inventory → Configuration → Warehouse Management → Storage Categories*):
  give a category a *Capacity by Package* line for a consolidatable package type
  (e.g. 5 per shelf) and assign the category to the locations. Nothing further is
  configured here - and core putaway respects the same limits for inbound stock.

Package consolidation
=====================

* Open *Inventory → Operations → Consolidation → **Packages to Consolidate***.
* Lists every package that can be merged with at least one other of the same
  **product, package type and warehouse** without exceeding one package's
  capacity, grouped by product.
* Shows each package's product, warehouse, location, on-hand quantity, capacity
  and fill percentage.
* Launch the wizard with **Consolidate All** on a product group, or by ticking
  rows and pressing **Consolidate Selected**.
* The wizard defaults the target to the **fullest** package, so the least stock
  is moved, and any of the selected packages can be chosen instead.
* Confirming raises an internal transfer that moves each source package's stock
  into the target package - and, where sources sit in other locations of the
  warehouse, into the target's location - preserving each quant's lot.

Location consolidation
======================

* Open *Inventory → Operations → Consolidation → **Locations to Consolidate***.
* Lists the packages held in every internal location that holds at least one
  package but fewer than its storage category allows, grouped by product, so
  each group shows where that product's packages are scattered.
* Shows each package's location alongside that location's package count and
  capacity.
* Launch the wizard with **Relocate All** on a product group, or by ticking rows
  and pressing **Relocate Selected**.
* The wizard offers same-warehouse locations with enough free slots and defaults
  to the **tightest fit** - filling the fullest location frees the most others.
* Confirming raises an internal transfer that moves each package **whole** - the
  package, its contents and its lots are unchanged, only its location differs.
* The destination is validated with core's
  ``stock.location._check_can_be_used``, so the storage category's package
  capacity, ``max_weight`` and *Allow New Product* policy all apply.

Models and fields
=================

* ``consolidation.package.capacity`` - the capacity master, unique per
  ``(product, package type)``, capacity must be positive.
* ``stock.package.type`` - adds ``can_be_consolidated``.
* ``stock.package`` - adds ``package_product_id``, ``content_qty``,
  ``reserved_qty``, ``capacity_qty``, ``remaining_qty`` and ``fill_pct``, all
  derived live from the package's quants.
* ``stock.location`` - adds ``package_capacity``, ``package_count`` and
  ``free_package_slots``, derived from the location's storage category.
* ``consolidation.package.line`` / ``consolidation.location.line`` - transient
  snapshots backing the two screens.
* ``consolidation.package.wizard`` / ``consolidation.location.wizard`` - the two
  wizards that raise the transfers.

Menus
=====

* *Inventory → Operations → Consolidation* - **Packages to Consolidate** and
  **Locations to Consolidate**.
* *Inventory → Products → Consolidatable Packages* - every consolidatable
  package with its live fill level.
* *Inventory → Configuration → Products → Package Capacities* - the capacity
  master.
