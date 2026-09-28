import {Component, onMounted, onWillUnmount, useState, xml} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

class InstantPaymentDialog extends Component {
    static template = xml`
        <Dialog title="'MOTO Payment'">
            <div class="d-flex flex-column align-items-center justify-content-center py-4 gap-3">
                <t t-if="state.windowOpen">
                    <i class="fa fa-clock-o fa-2x text-primary"/>
                    <p class="mb-0">Complete payment in the payment window.</p>
                    <p class="text-muted small mb-0">
                        Closed it by mistake?
                        <a href="#" t-on-click.prevent="openPaymentWindow">Reopen the payment window.</a>
                    </p>
                </t>
                <t t-else="">
                    <p class="text-muted mb-0">Open the payment window to take payment for this order.</p>
                    <button class="btn btn-primary" t-on-click="openPaymentWindow">
                        Open Payment Window
                    </button>
                </t>
            </div>
        </Dialog>
    `;
    static components = {Dialog};

    setup() {
        this.actionService = useService("action");
        this.state = useState({windowOpen: false});
        this._popupWindow = null;
        this._pollTimer = null;
        this._messageReceived = false;
        this._onMessage = this._onMessage.bind(this);
        onMounted(() => window.addEventListener("message", this._onMessage));
        onWillUnmount(() => {
            window.removeEventListener("message", this._onMessage);
            clearInterval(this._pollTimer);
        });
    }

    openPaymentWindow() {
        if (this._popupWindow && !this._popupWindow.closed) {
            this._popupWindow.focus();
            return;
        }

        clearInterval(this._pollTimer);
        this._messageReceived = false;
        const w = 680,
            h = 700;
        const left = Math.round(window.screenX + (window.outerWidth - w) / 2);
        const top = Math.round(window.screenY + (window.outerHeight - h) / 2);
        this._popupWindow = window.open(
            this.props.url,
            "InstantPayment",
            `width=${w},height=${h},left=${left},top=${top}`
        );
        this.state.windowOpen = true;

        this._pollTimer = setInterval(() => {
            if (this._popupWindow && this._popupWindow.closed) {
                clearInterval(this._pollTimer);
                this.state.windowOpen = false;
                if (!this._messageReceived) {
                    this.props.close();
                }
            }
        }, 500);
    }

    _onMessage(ev) {
        if (ev.source !== this._popupWindow) return;
        if (ev.data === "payment_done") {
            this._messageReceived = true;
            clearInterval(this._pollTimer);
            this.props.close();
            this.actionService.doAction({
                type: "ir.actions.client",
                tag: "soft_reload",
            });
        }
    }
}

registry.category("actions").add("sale_moto_payment.PaymentDialog", (env, action) => {
    const orderId = action.context.active_id;
    env.services.dialog.add(InstantPaymentDialog, {
        url: `/sale_moto_payment/pay/${orderId}`,
    });
});
