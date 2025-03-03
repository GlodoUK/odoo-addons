odoo.define("web_leaflet.LeafletModel", function(require) {
    "use strict";
    var AbstractModel = require("web.AbstractModel");
    var LeafletModel = AbstractModel.extend({
        init: function() {
            this._super.apply(this, arguments);
            this.data = {};
        },

        get: function() {
            return this.data;
        },

        load: function(params) {
            this.data.count = 0;
            this.data.offset = 0;
            this.data.limit = 80;

            this.model = params.modelName;
            this.context = params.context;
            this.fields = params.fieldNames;
            this.domain = params.domain;
            this.params = params;
            this.orderBy = params.orderBy;

            return this._fetchData();
        },

        reload: function(handle, params) {
            var options = params || {};
            if (options.domain !== undefined) {
                this.domain = options.domain;
            }
            if (options.limit !== undefined) {
                this.data.limit = options.limit;
            }
            if (options.offset !== undefined) {
                this.data.offset = options.offset;
            }
            return this._fetchData();
        },

        _fetchData: async function() {
            var results = await this._fetchRecordData();
            this.data.records = results.records;
            this.data.count = results.length;
        },

        _fetchRecordData: function() {
            return this._rpc({
                route: "/web/dataset/search_read",
                model: this.model,
                context: this.context,
                fields: this.fields,
                domain: this.domain,
                orderBy: this.orderBy,
                limit: this.data.limit,
                offset: this.data.offset,
            });
        },
    });
    return LeafletModel;
});
