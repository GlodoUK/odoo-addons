import {Component} from "@odoo/owl";

export default class ProductTmplAttrib extends Component {
    static template = "cpq.ProductTmplAttrib";
    static props = {
        id: Number,
        attribute: {
            type: Object,
            shape: {
                id: Number,
                name: String,
                display_type: {
                    type: String,
                    validate: (type) =>
                        ["color", "pills", "radio", "select"].includes(type),
                },
                ptav_ids: {
                    type: Array,
                    element: {
                        type: Object,
                        shape: {
                            id: Number,
                            name: String,
                            html_color: [Boolean, String],
                            is_custom: Boolean,
                            price_extra: Number,
                            excluded: {type: Boolean, optional: true},
                            cpq_custom_type: [Boolean, String],
                            cpq_selection_values: {
                                optional: true,
                                type: Array,
                                element: {
                                    type: Array,
                                },
                            },
                        },
                    },
                },
            },
        },
        selected: {type: Object},
        onSelect: Function,
        onCustom: Function,
    };

    getPTAVTemplate() {
        switch (this.props.attribute.display_type) {
            case "color":
                return "cpq.ProductTmplAttribColor";
            case "pills":
            case "radio":
                return "cpq.ProductTmplAttribRadio";
            case "select":
                return "cpq.ProductTmplAttribSelect";
            default:
                return "cpq.ProductTmplAttribSelect";
        }
    }

    isSelected(ptavId) {
        return Object.prototype.hasOwnProperty.call(this.props.selected, ptavId);
    }

    get hasCustomPTAV() {
        return this.props.attribute.ptav_ids.some((ptav) => ptav.is_custom);
    }

    get selectedCustomPTAVs() {
        return this.props.attribute.ptav_ids.filter(
            (ptav) => ptav.is_custom && this.isSelected(ptav.id)
        );
    }

    onSelect(ev) {
        this.props.onSelect(this.props.id, ev.target.value);
    }

    onCustom(ptavId, ev) {
        this.props.onCustom(ptavId, ev.target.value);
    }

    onCustomInput(ev) {
        const ptavId = parseInt(ev.target.dataset.ptavId, 10);
        this.props.onCustom(ptavId, ev.target.value);
    }

    getCustomInputType(ptav) {
        if ([false, "char"].includes(ptav.cpq_custom_type)) {
            return "text";
        }
        if (["float", "integer"].includes(ptav.cpq_custom_type)) {
            return "number";
        }
        return "text";
    }

    getCustomStep(ptav) {
        if (ptav.cpq_custom_type === "float") {
            return "0.01";
        }
        if (ptav.cpq_custom_type === "integer") {
            return "1";
        }
        return undefined;
    }
}
