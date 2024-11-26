odoo.define("web_no_form_quick_edit.FormController", function (require) {
    "use strict";

    const FormController = require("web.FormController");

    FormController.include({
        _onQuickEdit: function (ev) {
            ev.stopPropagation();
        },
    });
});
