odoo.define("web_leaflet.LeafletController", function(require) {
    "use strict";
    var AbstractController = require("web.AbstractController");
    var Pager = require("web.Pager");
    var LeafletController = AbstractController.extend({
        custom_events: _.extend({}, AbstractController.prototype.custom_events, {
            open_clicked: "_onOpenClicked",
        }),

        renderPager: function($node) {
            const params = this._getPagerParams();
            this.pager = new Pager(this, params.size, params.current_min, params.limit);
            this.pager.on("pager_changed", this, newState => {
                this.pager.disable();
                this.reload({
                    limit: newState.limit,
                    offset: newState.current_min - 1,
                }).then(this.pager.enable.bind(this.pager));
            });
            return this.pager.appendTo($node);
        },

        update: function() {
            return this._super.apply(this, arguments).then(() => {
                this._updatePager();
            });
        },

        _getPagerParams: function() {
            const state = this.model.get();
            return {
                current_min: state.offset + 1,
                limit: state.limit,
                size: state.count,
            };
        },

        _updatePager: function() {
            if (this.pager) {
                this.pager.updateState(this._getPagerParams());
            }
        },

        _onOpenClicked: function(ev) {
            this.trigger_up("switch_view", {
                view_type: "form",
                res_id: ev.data.id,
                mode: "readonly",
                model: this.modelName,
            });
        },
    });
    return LeafletController;
});
