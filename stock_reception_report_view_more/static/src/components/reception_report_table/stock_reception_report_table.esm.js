import {ReceptionReportTable} from "@stock/components/reception_report_table/stock_reception_report_table";
import {patch} from "@web/core/utils/patch";

patch(ReceptionReportTable.prototype, {
    async onClickAssignAll() {
        // Extra lines are never assigned in bulk.
        const moveIds = [];
        const quantities = [];
        const inIds = [];
        for (const line of this.props.lines) {
            if (line.is_assigned || line.is_extra) {
                continue;
            }
            moveIds.push(line.move_out_id);
            quantities.push(line.quantity);
            inIds.push(line.move_ins);
        }
        if (!moveIds.length) {
            return;
        }
        await this.ormService.call("report.stock.report_reception", "action_assign", [
            false,
            moveIds,
            quantities,
            inIds,
        ]);
        this.env.bus.trigger("update-assign-state", {
            isAssigned: true,
            tableIndex: this.props.index,
        });
    },

    get hasAssignAllButton() {
        return this.props.lines.some(
            (line) => line.is_qty_assignable && !line.is_extra
        );
    },

    get isAssignAllDisabled() {
        return this.props.lines.every((line) => line.is_assigned || line.is_extra);
    },
});
