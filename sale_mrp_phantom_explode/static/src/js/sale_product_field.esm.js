import {PhantomExplodeDialog} from "./phantom_explode_dialog/phantom_explode_dialog.esm";
import {SaleOrderLineProductField} from "@sale/js/sale_product_field";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(SaleOrderLineProductField.prototype, {
    async _onProductUpdate() {
        super._onProductUpdate(...arguments);

        // Cheap filter (related to product.template); skips the RPC for
        // the vast majority of products that have no explodable phantom kit.
        if (!this.props.record.data.can_sale_mrp_phantom_explode) {
            return;
        }

        const initialQuantity = this.props.record.data.product_uom_qty || 1;
        const explodeInfo = await this._fetchSaleMrpPhantomExplodeInfo(initialQuantity);
        if (!explodeInfo) {
            return;
        }

        if (explodeInfo.mode === "always") {
            // The BoM mandates the explosion: no dialog, just do it.
            await this._doSaleMrpPhantomExplode(initialQuantity, explodeInfo);
            return;
        }

        this.dialog.add(PhantomExplodeDialog, {
            quantity: initialQuantity,
            confirm: (quantity) => this._doSaleMrpPhantomExplode(quantity, explodeInfo),
        });
    },

    async _fetchSaleMrpPhantomExplodeInfo(quantity) {
        const result = await this.orm.call(
            "product.product",
            "sale_mrp_phantom_explode",
            [this.props.record.data.product_id.id, quantity],
            {
                context: this.context,
                // No_variant attribute values selected on the line: bom lines
                // using "Apply on Variants" with such values are kept/skipped
                // based on these.
                never_attribute_value_ids: this._getNoVariantPtavIds(
                    this.props.record.data
                ),
            }
        );

        return result !== false && result.component_count > 0 ? result : false;
    },

    /**
     * Replace the kit line by its component lines.
     *
     * Combo pattern (see handleComboSave in @sale/js/sale_product_field):
     * setting a transient trigger field hands the explosion to the sale.order
     * onchange, so the kit line is replaced server-side in a single onchange
     * round-trip and the component lines come back with all computed fields
     * (description, price, taxes) filled in. Building the lines client-side
     * instead either "ticks" them in one at a time (one onchange per line) or
     * loses the computed fields (the onchange protocol baselines client-sent
     * CREATE values) - see the onchange docstring in models/product_template.py.
     *
     * @param {Number} quantity The kit quantity to explode.
     * @param {Object} explodeInfo The result of the sale_mrp_phantom_explode RPC.
     */
    async _doSaleMrpPhantomExplode(quantity, explodeInfo) {
        const lineList = this.props.record.model.root.data.order_line;
        await lineList.leaveEditMode();

        await this.props.record.update({
            product_uom_qty: quantity,
            sale_mrp_phantom_explode_requested: true,
        });
        // Ensure that the order lines are sorted according to their sequence;
        // the onchange resequenced them so the components take the kit line's
        // position. Same call as core's handleComboSave.
        await lineList._sort();

        this.notification.add(
            _t("Kit exploded into %s component lines.", explodeInfo.component_count),
            {type: "info"}
        );
    },
});
