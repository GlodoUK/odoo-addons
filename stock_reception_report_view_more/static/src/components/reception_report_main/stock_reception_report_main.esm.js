import {ReceptionReportMain} from "@stock/components/reception_report_main/stock_reception_report_main";
import {patch} from "@web/core/utils/patch";
import {useState} from "@odoo/owl";

patch(ReceptionReportMain.prototype, {
    setup() {
        super.setup(...arguments);
        this.viewMore = useState({showAll: false});
    },

    onClickViewMore() {
        this.viewMore.showAll = !this.viewMore.showAll;
    },

    async onClickAssignAll() {
        // Extra lines are never assigned in bulk.
        const moveIds = [];
        const quantities = [];
        const inIds = [];
        for (const lines of Object.values(this.state.sourcesToLines)) {
            for (const line of lines) {
                if (line.is_assigned || line.is_extra) {
                    continue;
                }
                moveIds.push(line.move_out_id);
                quantities.push(line.quantity);
                inIds.push(line.move_ins);
            }
        }
        await this.ormService.call("report.stock.report_reception", "action_assign", [
            false,
            moveIds,
            quantities,
            inIds,
        ]);
        for (const lines of Object.values(this.state.sourcesToLines)) {
            for (const line of lines) {
                if (!line.is_extra) {
                    line.is_assigned = true;
                }
            }
        }
    },

    get hasExtraLines() {
        return Object.values(this.state.sourcesToLines).some((lines) =>
            lines.some((line) => line.is_extra)
        );
    },

    get visibleSourcesToLines() {
        const result = {};
        // Moves whose line is part-fulfilled; their "expected" remainder lines
        // are folded into the full quantity when viewing more.
        const fullMoveIds = new Set();
        if (this.viewMore.showAll) {
            for (const lines of Object.values(this.state.sourcesToLines)) {
                for (const line of lines) {
                    if (line.full_quantity) {
                        fullMoveIds.add(line.move_out_id);
                    }
                }
            }
        }
        for (const [source, allLines] of Object.entries(this.state.sourcesToLines)) {
            let lines = allLines;
            if (this.viewMore.showAll) {
                lines = allLines
                    .filter(
                        (line) =>
                            line.is_qty_assignable || !fullMoveIds.has(line.move_out_id)
                    )
                    .map((line) =>
                        line.full_quantity && !line.is_assigned
                            ? {
                                  ...line,
                                  quantity: line.full_quantity,
                                  assign_quantity: line.quantity,
                              }
                            : line
                    );
            }
            const visible = this.viewMore.showAll
                ? lines
                : lines.filter((line) => !line.is_extra);
            if (visible.length) {
                result[source] = visible;
            }
        }
        return result;
    },

    get hasContent() {
        return Object.keys(this.visibleSourcesToLines).length > 0;
    },

    get isAssignAllDisabled() {
        return Object.values(this.state.sourcesToLines).every((lines) =>
            lines.every(
                (line) => line.is_extra || line.is_assigned || !line.is_qty_assignable
            )
        );
    },
});
