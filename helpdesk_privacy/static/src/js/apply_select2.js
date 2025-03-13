odoo.define("helpdesk_privacy.select2", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.websiteSelect2Selection = publicWidget.Widget.extend({
        selector: ".glo_select2_selection",
        start: function () {
            this.$el.select2({
                allowClear: true,
            });
        },
    });
});
