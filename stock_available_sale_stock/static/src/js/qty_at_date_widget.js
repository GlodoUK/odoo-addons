odoo.define("stock_available_sale_stock.QtyAtDateWidget", function (require) {
    "use strict";

    var utils = require("web.utils");
    var QtyAtDateWidget = require("sale_stock.QtyAtDateWidget");

    QtyAtDateWidget.include({
        _updateData: function () {
            this._super.apply(this, arguments);

            if (this.data.qty_immediately_usable_today) {
                var qty_to_deliver = utils.round_decimals(
                    this.data.qty_to_deliver,
                    this.fields.qty_to_deliver.digits[1]
                );
                this.data.will_be_fulfilled =
                    utils.round_decimals(
                        this.data.qty_immediately_usable_today,
                        this.fields.qty_immediately_usable_today.digits[1]
                    ) >= qty_to_deliver;
            }

            // Re-run the upstream functionality as we've potentially changed the will_be_fulfilled field
            if (["draft", "sent"].includes(this.data.state)) {
                // Moves aren't created yet, then the forecasted is only based on virtual_available of quant
                this.data.forecasted_issue =
                    !this.data.will_be_fulfilled && !this.data.is_mto;
            } else {
                // Moves are created, using the forecasted data of related moves
                this.data.forecasted_issue =
                    !this.data.will_be_fulfilled || this.data.will_be_late;
            }
        },
    });
});
