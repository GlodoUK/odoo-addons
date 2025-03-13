odoo.define("helpdesk_privacy.ticket_actions", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.websiteTicketActions = publicWidget.Widget.extend({
        selector: "#privacy",
        events: {
            change: "_onChangePrivacy",
        },
        start: function () {
            this._showFollowersDuePrivacy(this.$el);
        },
        _showFollowersDuePrivacy: function (target) {
            if (target.length === 1) {
                const followers_div = document.getElementById("add_followers");
                if (target[0].checked === true) {
                    followers_div.style.display = "none";
                } else {
                    followers_div.style.display = "block";
                }
            }
        },
        _onChangePrivacy: function (ev) {
            const target = $(ev.currentTarget);
            this._showFollowersDuePrivacy(target);
        },
    });
});
