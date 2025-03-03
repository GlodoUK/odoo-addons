===========
web_leaflet
===========

Creates a leaflet.js powered controller and view that renders a map.


Usage
=====

Create or modify an ir.actions.act_window to have a view_mode of leaflet

::

  <record id="action_my_act_window" model="ir.actions.act_window">
    <field name="view_mode">tree,kanban,form,leaflet</field>
  </record>


Create a view for your model, provide the lat/long fields, and then use like a kanban (note: not all features of a kanban's markup are correctly supported).

::

  <record model="ir.ui.view" id="my_view">

      <field name="name">my_view</field>
      <field name="model">a.model</field>
      <field name="arch" type="xml">
          <leaflet lat="latitude" long="longitude" fly="1">
              <!-- fields to fetch for each record for display -->
              <field name="display_name"/>
              <field name="id"/>

              <templates>
                  <t t-name="leaflet-marker-popup">
                      <-- markup inside of a leaflet marker popup -->

                      <div class="d-flex" style="min-width: 250px;">
                          <div t-attf-style="background-image: url('#{leaflet_image('a.model', 'main_image', record.id)}'); background-size: cover; background-position: center; background-repeat: no-repeat; flex: 1 0 96px; min-height: 96px; margin-right: 16px;">
                          </div>

                          <div style="padding-top: 10px; padding-bottom: 10px;">
                              <field name="display_name"/>
                          </div>
                      </div>
                  </t>
              </templates>
          </leaflet>
      </field>
  </record>
