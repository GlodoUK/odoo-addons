/** @odoo-module **/

import BarcodePickingModel from "@stock_barcode/models/barcode_picking_model";
import {patch} from "web.utils";

patch(BarcodePickingModel.prototype, "stock_barcode_putaway_rules", {
    async _applyPutawayRules() {
        await this.save();
        await this.orm.call(this.params.model, "apply_putaway_strategy", [
            [this.params.id],
        ]);
        this.trigger("refresh");
    },
});
