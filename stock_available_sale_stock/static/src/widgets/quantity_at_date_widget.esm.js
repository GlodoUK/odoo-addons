import {QtyAtDateWidget} from "@sale_stock/widgets/qty_at_date_widget";
import {patch} from "@web/core/utils/patch";
import {roundDecimals} from "@web/core/utils/numbers";

patch(QtyAtDateWidget.prototype, {
    initCalcData() {
        const res = super.initCalcData();

        const {data} = this.props.record;

        if (data.qty_immediately_usable_today) {
            const qty_to_deliver = roundDecimals(data.qty_to_deliver, 0.01);

            this.calcData.will_be_fulfilled =
                roundDecimals(data.qty_immediately_usable_today, 0.01) >=
                qty_to_deliver;
        }

        // Re-run the upstream functionality as we've potentially changed the will_be_fulfilled field
        this.calcData.will_be_late =
            data.forecast_expected_date &&
            data.forecast_expected_date > data.scheduled_date;
        if (["draft", "sent"].includes(data.state)) {
            // Moves aren't created yet, then the forecasted is only based on virtual_available of quant
            this.calcData.forecasted_issue =
                !this.calcData.will_be_fulfilled && !data.is_mto;
        } else {
            // Moves are created, using the forecasted data of related moves
            this.calcData.forecasted_issue =
                !this.calcData.will_be_fulfilled || this.calcData.will_be_late;
        }

        return res;
    },
});
