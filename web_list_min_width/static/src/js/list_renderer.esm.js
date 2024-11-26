/** @odoo-module **/

import {ListRenderer} from "@web/views/list/list_renderer";
import {patch} from "@web/core/utils/patch";

patch(ListRenderer.prototype, "web_list_min_width", {
    calculateColumnWidth(column) {
        // Backwards compat
        if (
            column.rawAttrs !== undefined &&
            column.rawAttrs["min-width"] !== undefined
        ) {
            return {
                type: "absolute",
                value: column.rawAttrs["min-width"],
            };
        }

        if (column.options !== undefined && column.options["min-width"] !== undefined) {
            return {
                type: "absolute",
                value: column.options["min-width"],
            };
        }

        return this._super(column);
    },
});
