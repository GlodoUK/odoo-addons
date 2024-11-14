odoo.define("web_html_code_view.field_html", function (require) {
    "use strict";

    var field_html = require("web_editor.field.html");

    field_html.include({
        _getWysiwygOptions: function () {
            var res = this._super.apply(this, arguments);

            var originalGenerateOptions = res.generateOptions;

            res.generateOptions = function (options) {
                var options = originalGenerateOptions(options);

                var toolbar = options.toolbar || options.airPopover || {};
                options.codeview = true;
                var view = _.find(toolbar, function (item) {
                    return item[0] === "view";
                });
                if (view) {
                    if (!view[1].includes("codeview")) {
                        view[1].splice(-1, 0, "codeview");
                    }
                } else {
                    toolbar.splice(-1, 0, ["view", ["codeview"]]);
                }

                return options;
            };

            return res;
        },
    });

    return field_html;
});
