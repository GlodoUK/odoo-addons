odoo.define("website.leaflet", function (require) {
    "use strict";
    /* global L*/

    var publicWidget = require("web.public.widget");

    const COLOURS = [
        "truck",
        "addr",
        "blue",
        "green",
        "yellow",
        "red",
        "grey",
        "violet",
        "black",
    ];

    publicWidget.registry.leafletMap = publicWidget.Widget.extend({
        selector: ".o_leaflet_map",

        start: function () {
            this._super.apply(this, arguments);

            this.leafletInitDone = false;
            this.leafletTileTemplate =
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png";

            var fieldLat = this.$target[0].dataset.lat;
            var fieldLong = this.$target[0].dataset.long;

            this.markerList = [];

            if (fieldLat && fieldLong) {
                this.markerList.push([undefined, fieldLat, fieldLong]);
            }

            if (this.$target[0].dataset.markers) {
                try {
                    var dataset = JSON.parse(this.$target[0].dataset.markers);
                    this.markerList = this.markerList.concat(dataset);
                } catch (e) {
                    console.error("Invalid Markers", e);
                }
            }

            this.initLeaflet();
        },

        initLeaflet: function () {
            if (this.leafletInitDone) {
                return;
            }

            var mapContainer = document.createElement("div");

            mapContainer.classList.add("o_leaflet_container", "col-md-12");
            this.el.appendChild(mapContainer);

            this.leafletMap = L.map(mapContainer, {
                maxBounds: [L.latLng(180, -180), L.latLng(-180, 180)],
            });

            L.tileLayer(this.leafletTileTemplate, {}).addTo(this.leafletMap);

            var self = this;

            $(window).resize(function () {
                // On resize we need to tell leaflet that the size has changed,
                // so that panTo, flyTo, etc. all work correctly.

                if (self.leafletMapResized) {
                    clearTimeout(self.leafletMapResized);
                }

                self.leafletMapResized = setTimeout(function () {
                    self.leafletMap.invalidateSize();
                }, 500);
            });

            this.leafletInitDone = true;

            this.icons = {};

            for (const i of COLOURS) {
                this.icons[i] = L.icon({
                    iconUrl:
                        "/website_leaflet/static/lib/leaflet/images/marker-icon-" +
                        i +
                        ".png",
                    iconRetinaUrl:
                        "/website_leaflet/static/lib/leaflet/images/marker-icon-" +
                        i +
                        ".png",
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    tooltipAnchor: [16, -28],
                    shadowSize: [41, 41],
                    shadowUrl:
                        "/website_leaflet/static/lib/leaflet/images/marker-shadow.png",
                });
            }

            this._addMarkers();
        },

        _addMarkers: function () {
            if (!this.leafletInitDone) {
                return;
            }

            this.markerIndex = [];
            this.markerBounds = [];

            if (this.markerList) {
                for (var i = 0; i < this.markerList.length; i++) {
                    var options = {};

                    if (this.icons[this.markerList[i][0]]) {
                        options.icon = this.icons[this.markerList[i][0]];
                    }

                    var markerTemp = L.marker(
                        [this.markerList[i][1], this.markerList[i][2]],
                        options
                    );
                    markerTemp.addTo(this.leafletMap);
                    this.markerIndex.push(markerTemp);

                    var bounds = [this.markerList[i][1], this.markerList[i][2]];
                    this.markerBounds.push(bounds);
                }
            }

            this.leafletMap.fitBounds(this.markerBounds);
        },

        destroy: function () {
            for (var i = 0; i < this.markerList.length; i++) {
                this.markerList[i].off("click");
            }

            if (this.leafletMapResized) {
                clearTimeout(this.leafletMapResized);
            }

            this.leafletMap.remove();
            this.leafletInitDone = false;
            return this._super.apply(this, arguments);
        },
    });

    return publicWidget.registry.leafletMap;
});
