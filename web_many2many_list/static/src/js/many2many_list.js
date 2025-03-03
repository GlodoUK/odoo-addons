odoo.define('web_widget_many2many_list', function (require) {

"use strict";

var registry = require('web.field_registry');
var AbstractField = require('web.AbstractField');


var FieldMany2ManyList = AbstractField.extend({
    supportedFieldTypes: ['many2many'],
    init: function () {
        this._super.apply(this, arguments);

        const distinct = function(value, index, self) {
            return self.indexOf(value) == index;
        }

        const distinctData = this.value.data.map(function(r) { return r.data.display_name; }).filter(distinct);

        this.m2mValues_text = distinctData.join(", ");
    },

    fieldsToFetch: {
        display_name: {type: 'char'},
    },

    _renderList: function () {
        this.$el.text(
            this.m2mValues_text
        );
    },

    _renderEdit: function () {
        this._renderList();
    },

    _renderReadonly: function () {
        this._renderList();
    },
});


registry.add('many2many_list', FieldMany2ManyList);

return {
    FieldMany2ManyList: FieldMany2ManyList
}

});
