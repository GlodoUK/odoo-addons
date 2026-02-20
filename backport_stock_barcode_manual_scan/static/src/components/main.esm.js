/** @odoo-module **/

import MainComponent from "@stock_barcode/components/main";
import {patch} from "web.utils";

patch(MainComponent.prototype, "backport_stock_barcode_manual_scan", {
    barcodeManualScan() {
        const barcode = window.prompt("Enter a barcode"); // eslint-disable-line no-alert
        if (barcode !== null) {
            this.env.model.processBarcode(barcode.trim());
        }
    },
});
