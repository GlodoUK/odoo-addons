odoo.define(
    "product_meta_sale_product_configurator.product_configurator",
    function (require) {
        "use strict";

        var SaleProductConfiguratorWidget = require("sale_product_configurator.product_configurator");

        var MetaProductConfiguratorWidget = SaleProductConfiguratorWidget.include({
            _getMainProductChanges: function (mainProduct) {
                // Insert the meta attrs so that they are propapated to the server
                // to deal with
                const res = this._super.apply(this, arguments);

                if ("meta_attrs" in mainProduct) {
                    res.meta_attrs = mainProduct.meta_attrs;
                }

                return res;
            },
        });

        return MetaProductConfiguratorWidget;
    }
);
