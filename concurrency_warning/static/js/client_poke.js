odoo.define("glodo_helpdesk_live_update.client_poke", function (require) {
    "use strict";

    var Core = require("web.core");
    var _t = Core._t;
    var Session = require("web.session");
    var WebClient = require("web.WebClient");

    WebClient.include({
        start: function () {
            // Debounce the poke notification (on the leading edge), so a user does
            // not receive multiple alerts when multiple writes happen in quick
            // succession
            this.onPoke = _.debounce(this.onPoke, 2000, true);
            this._super.apply(this, arguments);
        },
        show_application: function () {
            console.log("Edit Notifications Ready");
            this.call("bus_service", "addChannel", "poke");
            this.call("bus_service", "onNotification", this, this.onNotification);
            return this._super.apply(this, arguments);
        },
        onNotification: function (notifications) {
            var that = this;
            _.each(
                notifications,
                function (notification, idx) {
                    if (notification[0] == "poke") {
                        this.onPoke(notification[1]);
                    }
                },
                this
            );
        },
        onPoke: function (message) {
            var action = this.action_manager.getCurrentAction();
            var controller = this.action_manager.getCurrentController();

            // Did we get the action and controller? Are we the same user?
            if (!action || !controller || Session.uid === message.uid) return;

            // Not 100% happy with this but it seems to be the most
            // "persistent" way of getting the current record ID.
            const currentId = parseInt(this._current_state.id);
            // Are we looking at the same individual record?
            if (
                controller.widget.modelName === message.model &&
                !controller.widget.isMultiRecord &&
                message.ids.includes(currentId)
            ) {
                controller.widget.reload();
                this.do_warn(
                    _t("Warning"),
                    _.str.sprintf(
                        _t(
                            "This record has been changed by another user (%s) since you opened it. The record has been automatically refreshed."
                        ),
                        message.username
                    ),
                    false
                );
            }
        },
    });
});
