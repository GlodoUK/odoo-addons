import ConfigureDialog from "@cpq/components/dialog/dialog.esm";
import {SaleOrderLineProductField} from "@sale/js/sale_product_field";
import {patch} from "@web/core/utils/patch";

patch(SaleOrderLineProductField.prototype, {
    get isCpq() {
        return this.props.record.data.product_template_id_cpq_ok;
    },

    async _onProductTemplateUpdate() {
        if (this.isCpq) {
            return this._openCpqConfigurator(false);
        }
        return super._onProductTemplateUpdate(...arguments);
    },

    onEditConfiguration() {
        if (this.isCpq) {
            return this._openCpqConfigurator(true);
        }
        return super.onEditConfiguration(...arguments);
    },

    async _openCpqConfigurator(edit = false) {
        const record = this.props.record;
        const saleOrderRecord = record.model.root;
        const productTmplId = record.data.product_template_id.id;

        let combination = {};

        if (edit && record.data.product_id) {
            combination = await this.orm.call(
                "product.product",
                "cpq_combination_tuples",
                [record.data.product_id.id]
            );
        }

        this.dialog.add(ConfigureDialog, {
            productTmplId: productTmplId,
            combination: combination,

            save: async (_resultTmplId, productId) => {
                await record.update({
                    product_id: {id: productId},
                });
            },
            discard: () => {
                if (!edit) {
                    saleOrderRecord.data.order_line.delete(record);
                }
            },
        });
    },
});
