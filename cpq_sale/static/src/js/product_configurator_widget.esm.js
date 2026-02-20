import {patch} from "@web/core/utils/patch";
import {SaleOrderLineProductField} from "@sale/js/sale_product_field";
import ConfigureDialog from "@cpq/components/dialog/dialog.esm";

patch(SaleOrderLineProductField.prototype, {
    get isCpq() {
        return this.props.record.data.product_template_id_cpq_ok;
    },

    async _onProductTemplateUpdate() {
        if (this.isCpq) {
            return this._openCpqConfigurator();
        }
        return super._onProductTemplateUpdate(...arguments);
    },

    onEditConfiguration() {
        if (this.isCpq) {
            return this._openCpqConfigurator(true);
        }
        return super.onEditConfiguration(...arguments);
    },

    _openCpqConfigurator(edit = false) {
        const record = this.props.record;
        const saleOrderRecord = record.model.root;

        const props = {
            productTmplId: record.data.product_template_id.id,
            save: async (productTmplId, productId) => {
                await record.update({
                    product_id: {id: productId},
                });
            },
            discard: edit
                ? () => {}
                : () => {
                      saleOrderRecord.data.order_line.delete(record);
                  },
        };

        if (edit && record.data.product_id) {
            props.productId = record.data.product_id.id;
        }

        this.dialog.add(ConfigureDialog, props);
    },
});
