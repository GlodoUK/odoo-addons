odoo.define("web_leaflet.LeafletView", function(require) {
    "use strict";

    var LeafletModel = require("web_leaflet.LeafletModel");
    var LeafletController = require("web_leaflet.LeafletController");
    var LeafletRenderer = require("web_leaflet.LeafletRenderer");
    var AbstractView = require("web.AbstractView");
    var viewRegistry = require("web.view_registry");
    var _t = require("web.core")._t;

    var LeafletView = AbstractView.extend({
        jsLibs: ["/web_leaflet/static/lib/leaflet/leaflet.js"],
        config: _.extend({}, AbstractView.prototype.config, {
            Model: LeafletModel,
            Controller: LeafletController,
            Renderer: LeafletRenderer,
        }),
        icon: "fa-map-marker",
        display_name: "Leaflet Map",
        viewType: "leaflet",
        mobile_friendly: true,
        searchMenuTypes: ["filter", "favorite"],

        init: function(viewInfo, params) {
            this._super.apply(this, arguments);

            var fieldNames = [];

            fieldNames.push(this.arch.attrs.lat);
            fieldNames.push(this.arch.attrs.long);
            fieldNames.push("display_name");

            this.arch.children.forEach(function(node) {
                if (node.tag === "field") {
                    fieldNames.push(node.attrs.name);
                }
            });

            this.rendererParams.lat = this.arch.attrs.lat;
            this.rendererParams.long = this.arch.attrs.long;
            this.rendererParams.fly = this.arch.attrs.fly;
            this.rendererParams.flyZoom = this.arch.attrs.fly_zoom;

            this.rendererParams.defaultOrder = this.arch.attrs.default_order;
            this.rendererParams.panelTitle =
                this.arch.attrs.panel_title || params.displayName || _t("Items");
        },
    });
    viewRegistry.add("leaflet", LeafletView);
    return LeafletView;
});
