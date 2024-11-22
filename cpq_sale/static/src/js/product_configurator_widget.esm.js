/** @odoo-module **/
/* eslint-disable sort-imports */

import {ConfigureDialog} from "@cpq/components/dialog/dialog.esm";
import {patch} from "@web/core/utils/patch";
import {SaleOrderLineProductField} from "@sale/js/sale_product_field";
import {useService} from "@web/core/utils/hooks";

patch(SaleOrderLineProductField.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialogService = useService("dialog");
    },

    _editProductConfiguration() {
        if (this.props.record.data.product_template_id_cpq_ok) {
            return this._cpqConfigureDialog();
        }

        super._editProductConfiguration(...arguments);
    },

    async _onProductTemplateUpdate() {
        if (this.props.record.data.product_template_id_cpq_ok) {
            return this._cpqConfigureDialog();
        }
        super._onProductTemplateUpdate(...arguments);
    },

    async _openProductConfigurator(edit = false) {
        if (edit && this.props.record.data.product_template_id_cpq_ok) {
            return this._cpqConfigureDialog();
        }
        super._openProductConfigurator(...arguments);
    },

    _cpqConfigureDialog() {
        this.dialogService.add(ConfigureDialog, {
            productTmplId: this.props.record.data.product_template_id[0],
            edit: true,
            save: async (productTmplId, productId) => {
                const result = await this.orm.call(
                    "product.template",
                    "get_single_product_variant",
                    [this.props.record.data.product_template_id[0]],
                    {
                        context: this.context,
                    }
                );
                // Persist updated product_id and name
                await this.props.record.update({
                    product_id: [productId, result.product_name],
                });
            },
            discard: () => {
                this.props.record.update({product_id: false, name: false});
            },
        });
    },
});
