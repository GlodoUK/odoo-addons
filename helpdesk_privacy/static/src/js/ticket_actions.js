odoo.define("helpdesk_privacy.ticket_actions", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.websiteTicketPrivacyFollowers = publicWidget.Widget.extend({
        selector: ".helpdesk_privacy_followers",
        start: function () {
            $("select.js_select2").select2();
        },
    });
});
