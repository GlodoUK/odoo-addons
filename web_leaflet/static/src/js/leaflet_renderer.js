odoo.define("web_leaflet.LeafletRenderer", function(require) {
    "use strict";

    /* global L*/

    function findTemplates(node, predicate) {
        if (predicate(node)) {
            return node;
        }
        if (!node.children) {
            return undefined;
        }
        for (var i = 0; i < node.children.length; i++) {
            if (findTemplates(node.children[i], predicate)) {
                return node.children[i];
            }
        }
    }

    var core = require("web.core");
    var AbstractRenderer = require("web.AbstractRenderer");
    var field_utils = require("web.field_utils");
    var utils = require("web.utils");
    var qweb = core.qweb;
    var config = require("web.config");
    var session = require("web.session");
    var pyUtils = require("web.py_utils");
    var QWeb = require("web.QWeb");

    var LeafletRenderer = AbstractRenderer.extend({
        className: "o_leaflet_view row no-gutters",

        init: function(parent, state, params) {
            this._super.apply(this, arguments);
            this.fieldLat = params.lat;
            this.fieldLong = params.long;
            this.fly = Boolean(params.fly);
            this.flyZoom = params.flyZoom ? params.flyZoom : 12;
            this.panelTitle = params.panelTitle;

            this.active = false;
            this.leafletInitDone = false;
            this.markers = {};

            this.leafletTileTemplate =
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png";

            this.qweb = new QWeb(
                config.isDebug(),
                {
                    _s: session.origin,
                },
                false
            );

            var templates = findTemplates(this.arch, function(n) {
                return n.tag === "templates";
            });
            this.qweb.add_template(utils.json_node_to_xml(templates));
        },

        on_attach_callback: function() {
            this.active = true;
            this._initLeaflet();
            var latLngCollection = this._getLatLngCollection();
            if (latLngCollection) {
                this.leafletMap.fitBounds(latLngCollection);
            } else {
                this.leafletMap.fitWorld();
            }
            this._addMarkers(this.state.records);

            this._addMarkerList();
        },

        on_detach_callback: function() {
            this.active = false;
        },

        destroy: function() {
            Object.values(this.markers).forEach(function(marker) {
                marker.off("click");
            });

            if (this.leafletMapResized) {
                clearTimeout(this.leafletMapResized);
            }

            this.leafletMap.remove();
            return this._super.apply(this, arguments);
        },

        _initLeaflet: function() {
            if (this.leafletInitDone) {
                return;
            }
            this.leafletInitDone = true;
            var mapContainer = document.createElement("div");

            mapContainer.classList.add("o_leaflet_container", "col-md-12", "col-lg-10");
            this.el.appendChild(mapContainer);

            this.leafletMap = L.map(mapContainer, {
                maxBounds: [L.latLng(180, -180), L.latLng(-180, 180)],
            });

            L.tileLayer(this.leafletTileTemplate, {}).addTo(this.leafletMap);

            $(mapContainer).resize(function() {
                // On resize we need to tell leaflet that the size has changed,
                // so that panTo, flyTo, etc. all work correctly.

                if (this.leafletMapResized) {
                    clearTimeout(this.leafletMapResized);
                }

                this.leafletMapResized = setTimeout(function() {
                    this.leafletMap.invalidateSize();
                }, 500);
            });
        },

        _getLatLngCollection: function() {
            var self = this;
            var result = [];
            this.state.records.forEach(function(record) {
                if (record[self.fieldLat] && record[self.fieldLong]) {
                    result.push(
                        L.latLng(record[self.fieldLat], record[self.fieldLong])
                    );
                }
            });
            if (!result.length) {
                return false;
            }
            return L.latLngBounds(result);
        },

        _getImageURL: function(model, field, id, placeholder) {
            // TODO: This is a partial implementation of the same functionality you would see for kanban_image
            // It only supports a small subset of the functionality

            var current_id = (_.isArray(id) ? id[0] : id) || false;
            var url = placeholder || "/web/static/src/img/placeholder.png";

            if (model && field && current_id) {
                url = this.getSession().url("/web/image", {
                    model: model,
                    field: field,
                    id: current_id,
                });
            }
            return url;
        },

        _addMarkers: function(records) {
            var self = this;
            this._removeMarkers();

            if (!this.fieldLat || !this.fieldLong) {
                return;
            }

            records.forEach(function(record) {
                if (record[self.fieldLat] && record[self.fieldLong]) {
                    var $popup = self._renderMarker(record);

                    var marker = L.marker([
                        record[self.fieldLat],
                        record[self.fieldLong],
                    ]);
                    var offset = new L.Point(0, 0);
                    marker.addTo(self.leafletMap).bindPopup(
                        function() {
                            // We need to wrap each, popup so we can make our
                            // onclick trigger properly with leaflet.
                            // We cannot just assign it to $popup.

                            var $wrapped_popup = document.createElement("div");
                            $wrapped_popup.innerHTML = $popup.prop("outerHTML");
                            $wrapped_popup.onclick = function() {
                                self.trigger_up("open_clicked", {id: record.id});
                            };
                            $wrapped_popup.style = "cursor: pointer;";

                            return $wrapped_popup;
                        },
                        {offset: offset}
                    );
                    self.markers[record.id] = marker;
                }
            });
        },

        _renderMarker: function(record) {
            var content = $(
                this.qweb.render("leaflet-marker-popup", {
                    leaflet_image: this._getImageURL.bind(this),

                    record: record,
                    user_context: this.getSession().user_context,
                })
            );

            // Replace any field tags like the kanban does
            // TODO: This only supports a small subset of the functionality that the kanban does
            content.find("field").each(function() {
                var $field = $(this);

                var field_name = $field.attr("name");
                var field_widget = $field.attr("widget");
                var field_options = $field.attr("options");
                field_options = field_options ? pyUtils.py_eval(field_options) : {};

                if (field_widget === "monetary" && "currency_field" in field_options) {
                    var currency_field = record[field_options.currency_field];

                    if (_.isArray(currency_field)) {
                        currency_field = currency_field[0];
                    }

                    var currency = session.get_currency(currency_field);
                    field_options.currency = currency;
                    delete field_options.currency_field;
                }

                var value = record[field_name].toString();
                if (field_widget) {
                    value = field_utils.format[field_widget](
                        field_utils.parse[field_widget](value, {}),
                        {},
                        field_options
                    );

                    $field.replaceWith(
                        $("<span>", {
                            html: value,
                        })
                    );
                } else {
                    $field.replaceWith(
                        $("<span>", {
                            text: value,
                        })
                    );
                }
            });

            return content;
        },

        _addMarkerList: function() {
            this.$markerList = $(qweb.render("LeafletView.markerList", {widget: this}));
            var $container = this.$el.find(".o_marker_list_container");
            if ($container.length) {
                $container.replaceWith(this.$markerList);
            } else {
                this.$el.append(this.$markerList);
            }

            this.$(".o_marker_list_container li a").on(
                "click",
                this._centerAndOpenMarker.bind(this)
            );
        },

        _centerAndOpenMarker: function(ev) {
            ev.preventDefault();

            var marker = this.markers[ev.target.dataset.recordId];

            if (!marker) {
                return;
            }

            if (this.fly) {
                this.leafletMap.flyTo(marker._latlng, this.flyZoom, {
                    animate: true,
                    duration: 2,
                });
            } else {
                this.leafletMap.panTo(marker._latlng, {
                    animate: true,
                });
            }

            marker.openPopup();
        },

        _removeMarkers: function() {
            var self = this;
            Object.values(this.markers).forEach(function(marker) {
                self.leafletMap.removeLayer(marker);
            });
            this.markers = {};
        },

        _render: function() {
            if (this.active) {
                var latLngCollection = this._getLatLngCollection();
                if (latLngCollection) {
                    this.leafletMap.flyToBounds(latLngCollection, {
                        animate: true,
                    });
                } else {
                    this.leafletMap.fitWorld();
                }
                this._addMarkers(this.state.records);
                this._addMarkerList();
            }
            return Promise.resolve();
        },
    });

    return LeafletRenderer;
});
