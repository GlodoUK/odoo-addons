import {ReceptionReportLine} from "@stock/components/reception_report_line/stock_reception_report_line";
import {patch} from "@web/core/utils/patch";

patch(ReceptionReportLine.prototype, {
    async onClickAssign() {
        // With "View more" the line shows the full quantity the transfer needs,
        // but only what the incoming stock can cover may be assigned.
        const quantity = this.data.assign_quantity ?? this.data.quantity;
        await this.ormService.call("report.stock.report_reception", "action_assign", [
            false,
            [this.data.move_out_id],
            [quantity],
            [this.data.move_ins],
        ]);
        this.env.bus.trigger("update-assign-state", {
            isAssigned: true,
            tableIndex: this.props.parentIndex,
            lineIndex: this.data.index,
        });
    },
});
