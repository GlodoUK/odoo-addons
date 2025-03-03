odoo.define("web_export_view_in_action", function (require) {
    "use strict";

    var ListController = require("web.ListController");

    var core = require("web.core");
    var Sidebar = require("web.Sidebar");
    var session = require("web.session");
    var crash_manager = require("web.crash_manager");

    var QWeb = core.qweb;

    var _t = core._t;

    ListController.include({
        renderSidebar: function ($node) {
            var self = this;
            this._super.apply(this, arguments);

            if (!this.sidebar) return;

            for (var i = 0; i < this.sidebar.items.other.length; i++) {
                if (this.sidebar.items.other[i].label == "Export") {
                    this.sidebar.items.other[i].label = _t(
                        "Export (Import Compatible)"
                    );
                    break;
                }
            }

            this.sidebar.items.other.unshift({
                label: _t("Export (Verbatim)"),
                callback: Sidebar.prototype.on_sidebar_export_treeview_xls.bind(
                    this.sidebar
                ),
            });
        },
    });
});
