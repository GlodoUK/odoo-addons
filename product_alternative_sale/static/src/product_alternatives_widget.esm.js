import {Component} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardWidgetProps} from "@web/views/widgets/standard_widget_props";
import {usePopover} from "@web/core/popover/popover_hook";
import {useService} from "@web/core/utils/hooks";

export class ProductAlternativesPopover extends Component {
    static template = "product_alternative_sale.ProductAlternativesPopover";
    static props = {
        close: Function,
        alternatives: Array,
        remainingCount: Number,
        lineId: [Number, Boolean],
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
    }

    get title() {
        return _t("Alternative Products");
    }

    async viewCatalog() {
        const action = await this.orm.call(
            "sale.order.line",
            "action_view_alternatives_catalog",
            [[this.props.lineId]]
        );
        this.props.close();
        await this.action.doAction(action);
    }
}

export class ProductAlternativesWidget extends Component {
    static components = {Popover: ProductAlternativesPopover};
    static template = "product_alternative_sale.ProductAlternatives";
    static props = {...standardWidgetProps};

    setup() {
        this.popover = usePopover(this.constructor.components.Popover, {
            position: "top",
        });
        this.orm = useService("orm");
    }

    async showPopup(ev) {
        // Capture the target before awaiting: the browser nulls
        // ev.currentTarget once the handler yields (see sale_stock QtyAtDate).
        const target = ev.currentTarget;
        // Resolve the alternatives lazily, only now that the popover is opening.
        // Keyed on the product (always a real id) so this works on unsaved
        // lines; the server returns just the preview plus an "X more" count.
        const productId = this.props.record.data.product_id.id;
        const {alternatives, remaining} = await this.orm.call(
            "product.product",
            "get_alternatives_preview",
            [[productId]]
        );
        // The catalog button needs a saved line; new records carry a virtual
        // (string) resId, so only pass a numeric id.
        const resId = this.props.record.resId;
        this.popover.open(target, {
            alternatives,
            remainingCount: remaining,
            lineId: typeof resId === "number" ? resId : false,
        });
    }
}

export const productAlternativesWidget = {
    component: ProductAlternativesWidget,
    fieldDependencies: [
        {name: "display_alternatives_widget", type: "boolean"},
        {name: "product_id", type: "many2one"},
    ],
};

registry
    .category("view_widgets")
    .add("product_alternatives_widget", productAlternativesWidget);
