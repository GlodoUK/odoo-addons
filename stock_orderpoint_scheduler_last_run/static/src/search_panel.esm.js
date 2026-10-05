import {deserializeDateTime, formatDateTime} from "@web/core/l10n/dates";
import {onWillStart, useState} from "@odoo/owl";
import {StockOrderpointSearchPanel} from "@stock/views/search/stock_orderpoint_search_panel";
import {patch} from "@web/core/utils/patch";

patch(StockOrderpointSearchPanel.prototype, {
    setup() {
        super.setup(...arguments);
        this.schedulerLastRun = useState({value: false});
        onWillStart(async () => {
            const value = await this.orm.call(
                "stock.warehouse.orderpoint",
                "get_scheduler_last_run",
                []
            );
            this.schedulerLastRun.value = value ? deserializeDateTime(value) : false;
        });
    },

    get schedulerLastRunRelative() {
        return this.schedulerLastRun.value.toRelative();
    },

    get schedulerLastRunExact() {
        return formatDateTime(this.schedulerLastRun.value);
    },
});
