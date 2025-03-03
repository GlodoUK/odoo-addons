odoo.define('wwuk_no_swipe.', function (require) {
'use strict';

var FormRenderer = require('web.FormRenderer');

FormRenderer.include({
    _enableSwipe: function() {
        return;
    }
});

return FormRenderer;

});
