/** @odoo-module */

const {Component} = owl;

class ProductTmplAttrib extends Component {
    // --------------------------------------------------------------------------
    // Handlers
    // --------------------------------------------------------------------------
    //

    stringify() {
        return JSON.stringify(this.props.attribute);
    }

    // --------------------------------------------------------------------------
    // Private
    // --------------------------------------------------------------------------

    /**
     * Return template name to use by checking the display type in the props.
     *
     * Each attribute line can have one of this four display types:
     *      - 'Color'  : Display each attribute as a circle filled with said color.
     *      - 'Pills'  : Display each attribute as a rectangle-shaped element.
     *      - 'Radio'  : Display each attribute as a radio element.
     *      - 'Select' : Display each attribute in a selection tag.
     *
     * @returns {String} - The template name to use.
     */
    getPTAVTemplate() {
        switch (this.props.attribute.display_type) {
            case "color":
                return "cpq.ProductTmplAttrib-color";
            case "pills":
            case "radio":
                return "cpq.ProductTmplAttrib-radio";
            case "select":
                return "cpq.ProductTmplAttrib-select";
        }
    }

    isSelectedPTAVCustom() {
        if (!this.props.attribute || !this.props.selected) {
            return false;
        }

        if (!this.props.attribute.ptav_ids) {
            return false;
        }

        return false;
    }
}

ProductTmplAttrib.template = "cpq.ProductTmplAttrib";
ProductTmplAttrib.props = {
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
                        // Backend sends 'false' when there is no color
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
    selected: {
        type: Object,
        optional: true,
    },
    onSelect: {type: "function"},
    onCustom: {type: "function"},
};

export default ProductTmplAttrib;
