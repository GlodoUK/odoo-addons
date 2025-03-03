odoo.define('web_button_enable_with_no_record.listrenderer', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var _t = core._t;

var ListRenderer = require('web.ListRenderer');

ListRenderer.include({

    _renderButton: function (record, node) {
        var $button = this._super.apply(this, arguments);
        var self = this;

        if (!record.res_id && node.attrs && node.attrs.options && "enable_with_no_record" in node.attrs.options && node.attrs.options.enable_with_no_record) {
            $button.on("click", function (e) {
                e.stopPropagation();
                self.trigger_up('button_clicked', {
                    attrs: node.attrs,
                    record: record,
                });
            });
            $button.attr('disabled', false);
        }

        return $button;
    }

});

});
