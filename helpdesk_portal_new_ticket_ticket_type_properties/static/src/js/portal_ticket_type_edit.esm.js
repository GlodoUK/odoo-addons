import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";

publicWidget.registry.PortalTicketTypeEdit = publicWidget.Widget.extend({
    selector: "#helpdesk_ticket_new",

    events: {
        "change select[name='category']": "_onTicketTypeChange",
    },

    _onTicketTypeChange: function () {
        const target = $(this.$el.find(".ticket_type_id_container"));

        if (!target) {
            return;
        }

        const buttonSubmit = $(this.$el).find("button[name='submit']");

        if (buttonSubmit) {
            buttonSubmit.prop("disabled", true);
        }

        const $ticketTypeField = $(this.$el).find("select[name='category']");

        let ticketTypeId = $ticketTypeField.find(":selected").val();
        ticketTypeId = parseInt(ticketTypeId, 10);

        if (isNaN(ticketTypeId)) {
            target.html("");
            return;
        }

        const params = {
            ticket_type_id: ticketTypeId,
        };

        rpc("/my/tickets/get_ticket_type_info", params).then((ticketTypeData) => {
            target.html(ticketTypeData.template);

            if (buttonSubmit) {
                buttonSubmit.prop("disabled", false);
            }
        });
    },
});
