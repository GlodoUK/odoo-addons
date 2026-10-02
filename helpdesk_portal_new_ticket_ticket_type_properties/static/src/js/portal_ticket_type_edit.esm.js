import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

export class PortalTicketTypeEdit extends Interaction {
    static selector = "#helpdesk_ticket_new";

    dynamicContent = {
        "select[name='ticket_categ_id']": {"t-on-change": this.onTicketCategChange},
        "button[name='submit']": {"t-att-disabled": () => this.loading},
    };

    setup() {
        this.loading = false;
        this.request = null;
        this.container = this.el.querySelector(".ticket_type_id_container");
    }

    async onTicketCategChange(ev) {
        if (!this.container) {
            return;
        }

        const ticketTypeId = parseInt(ev.currentTarget.value, 10);

        if (isNaN(ticketTypeId)) {
            this.container.replaceChildren();
            return;
        }

        // Only the answer to the latest change may replace the fields
        const request = rpc("/my/tickets/get_ticket_type_info", {
            ticket_type_id: ticketTypeId,
        });
        this.request = request;
        this.loading = true;
        // Async handlers only refresh once they end: disable submit right away
        this.updateContent();

        try {
            const {template} = await this.waitFor(request);
            if (request === this.request) {
                this.container.innerHTML = template;
            }
        } finally {
            if (request === this.request) {
                this.loading = false;
            }
        }
    }
}

registry
    .category("public.interactions")
    .add(
        "helpdesk_portal_new_ticket_ticket_type_properties.portal_ticket_type_edit",
        PortalTicketTypeEdit
    );
