/** @odoo-module **/

import MainComponent from "@stock_barcode/components/main";
import {patch} from "web.utils";

patch(MainComponent.prototype, "stock_barcode_putaway_rules", {
    get showStockBarcodePutawayRules() {
        console.log(this.env.model.record);
        return (
            this.env.model.record &&
            this.env.model.record.show_stock_barcode_putaway_rules
        );
    },
    async applyStockBarcodePutawayRules() {
        await this.env.model._applyPutawayRules();
    },
});
