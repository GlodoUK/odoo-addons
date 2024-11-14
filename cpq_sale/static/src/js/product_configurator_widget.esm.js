/** @odoo-module **/

import ConfigureDialog from "@cpq/components/dialog/dialog.esm";
import ProductConfiguratorWidget from "sale_product_configurator.product_configurator";

ProductConfiguratorWidget.include({
    _onEditConfiguration: function () {
        if (this.recordData.product_template_id_cpq_ok) {
            this._cpqConfigureDialog(
                this.recordData.product_template_id.data.id,
                this.dataPointID
            );
            return;
        }

        this._super.apply(this, arguments);
    },

    _cpqConfigureDialog: function (productTemplateId, dataPointId) {
        // FIXME: This is the only way I could figure out to get the
        // Owl env in a legacy widget, in a time reasonable manner.
        // When ProductConfiguratorWidget is ported to Owl this can probably
        // go away
        const env = odoo.__WOWL_DEBUG__.root.env;
        const self = this;

        env.services.dialog.add(ConfigureDialog, {
            productTmplId: this.recordData.product_template_id.res_id,
            save: (productTmplId, productId) => {
                self.trigger_up("field_changed", {
                    changes: {
                        product_id: {id: productId},
                    },
                    dataPointID: dataPointId,
                });
            },
            discard: () => {
                self.trigger_up("field_changed", {
                    changes: {
                        product_id: false,
                        name: false,
                    },
                    dataPointID: dataPointId,
                });
            },
        });
    },

    _onTemplateChange: function (productTemplateId, dataPointId) {
        if (this.recordData.product_template_id_cpq_ok) {
            return this._cpqConfigureDialog(productTemplateId, dataPointId);
        }
        return this._super.apply(this, arguments);
    },
});
