import {Component, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {QuantityButtons} from "@sale/js/quantity_buttons/quantity_buttons";
import {_t} from "@web/core/l10n/translation";

export class PhantomExplodeDialog extends Component {
    static template = "sale_mrp_phantom_explode.PhantomExplodeDialog";
    static components = {Dialog, QuantityButtons};
    static props = {
        quantity: {type: Number, optional: true},
        confirm: Function,
        close: Function,
    };

    setup() {
        this.title = _t("Explode kit into components?");
        this.state = useState({
            quantity: this.props.quantity || 1,
        });
    }

    /**
     * Set the kit quantity to explode, clamped to a minimum of 1.
     *
     * @param {Number} quantity The new quantity.
     * @returns {Boolean} Whether the quantity was updated.
     */
    setQuantity(quantity) {
        this.state.quantity = quantity <= 0 ? 1 : quantity;
        return true;
    }

    async confirm() {
        await this.props.confirm(this.state.quantity);
        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}
