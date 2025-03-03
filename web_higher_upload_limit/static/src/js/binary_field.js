odoo.define('web_higher_upload_limit.web_higher_upload_limit', function (require) {
    "use strict";

    var core = require('web.core'),
        data = require('web.data'),
        basic_fields = require('web.basic_fields');

    var _t = core._t,
        FieldBinaryFile = basic_fields.FieldBinaryFile,
        FieldBinaryImage = basic_fields.FieldBinaryImage;

    var max_size = 150;

    FieldBinaryFile.include({
        init: function () {
            this._super.apply(this, arguments);
            this.max_upload_size = max_size * 1024 * 1024; // 150MB
        }
    })

    FieldBinaryImage.include({
        init: function () {
            this._super.apply(this, arguments);
            this.max_upload_size = max_size * 1024 * 1024; // 150MB
        }
    });

});
