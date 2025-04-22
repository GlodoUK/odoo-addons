===============
website_leaflet
===============

Creates a leaflet.js powered frontend widget.

Currently supports multiple markers, no other functionality.

TODO
====

* Areas/polygons
* Snippet/editor support

Usage
=====

Add the following markup to your frontend

::

  <div class="o_leaflet_map" t-attf-data-lat="#{record.latitude}" t-attf-data-long="#{record.longitude}">
  </div>

or...

::

  <div class="o_leaflet_map" t-attf-data-markers='[["truck", #{record.latitude}, #{record.longitude}], ["addr", #{record.partner_id.partner_latitude}, #{record.partner_id.partner_longitude}]]'>
  </div>

Available Marker Types: ['truck', 'addr', 'blue', 'green', 'yellow', 'red', 'grey', 'violet', 'black']

Thanks
======

- Coloured pins by https://github.com/pointhi/leaflet-color-markers
- 'Truck' and 'House' icons by https://fontawesome.com/
