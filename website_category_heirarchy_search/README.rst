Website Hierarchical Category Search
=====================================

An Odoo eCommerce snippet that lets visitors drill down through hierarchical product categories using cascading dropdowns. Designed for catalogs with multi-level structures (e.g. Make → Model → Year in automotive parts stores).

Features
--------

- Draggable website builder snippet with live preview
- Cascading dropdowns that progressively narrow category selection
- Live product counts displayed next to each option
- Keyboard entry within each dropdown (powered by Odoo's SelectMenu)
- Per-category visibility control without unpublishing
- Multi-website aware

Requirements
------------

- Odoo 19.0
- ``website_sale``

Configuration
-------------

1. Set up your category hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before using the snippet, ensure your product categories form a hierarchy in **Website → Configuration → eCommerce → Product Categories**. The snippet requires a single root category at the top of the tree (e.g. "Vehicles"), with child categories beneath it for each dropdown level.

2. Control category visibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To hide a category from the widget without unpublishing it:

1. Go to **Website → Configuration → eCommerce → Product Categories**
2. Open the category record
3. Uncheck **Show in Category Search Widget**

This hides the category from snippet dropdowns while keeping it available elsewhere in the shop.

3. Add the snippet to a page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Open the **Website Builder** and navigate to the page where you want the widget
2. In the snippet sidebar, find **Category Search** under the **Content** section
3. Drag it onto the page

4. Configure the snippet
~~~~~~~~~~~~~~~~~~~~~~~~~

With the snippet selected in the website builder, the options panel on the right provides:

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - **Root Category**
     - Vehicles
     - The top-level category to start the hierarchy from
   * - **Level Labels**
     - Make, Model, Year
     - Comma-separated labels for each dropdown level
   * - **Button Text**
     - Find Parts
     - Label for the search button
   * - **Shop URL**
     - /shop
     - Base URL used when navigating to search results

The number of dropdowns rendered matches the number of labels provided (or the actual depth of the category tree, whichever is shallower).

How it works
------------

When a visitor uses the widget:

1. Dropdowns are populated from the category tree rooted at the configured **Root Category**
2. Selecting a value at one level reveals the next level's options
3. Product counts are loaded on demand and shown next to each option
4. Clicking the search button navigates to ``{Shop URL}?category={deepest selected id}``

Selections are encoded in the URL as ``?vcats=id1,id2,id3``, allowing the browser back button to restore the previous state.

License
-------

LGPL-3
