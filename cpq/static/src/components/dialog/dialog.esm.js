import {Component, onWillStart, useState} from "@odoo/owl";
import {_lt, _t} from "@web/core/l10n/translation";

import ProductTmplAttrib from "./product_tmpl_attrib.esm";
import {Dialog} from "@web/core/dialog/dialog";
import {WarningDialog} from "@web/core/errors/error_dialogs";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

export default class ConfigureDialog extends Component {
    static template = "cpq.ConfigureDialog";
    static components = {Dialog, ProductTmplAttrib};
    static props = {
        productTmplId: Number,
        save: {type: Function, optional: true},
        discard: {type: Function, optional: true},
        close: Function,
        size: {
            type: String,
            optional: true,
            validate: (s) => ["sm", "md", "lg", "xl", "fs", "fullscreen"].includes(s),
        },
    };

    setup() {
        this.title = _t("Configure");
        this.state = useState({
            ptalIds: [],
            selected: {},
            productTmpl: null,
            valid: false,
            errors: {},
            creating: false,
        });

        onWillStart(async () => {
            const data = await this._loadData();
            this.state.ptalIds = data.ptal_ids || [];
            this.state.productTmpl = data.product_tmpl_id;
            this.title = _t("Configure: %s", data.product_tmpl_id.display_name);
        });
    }

    async _loadData() {
        return rpc(`/cpq/${this.props.productTmplId}/data`, {});
    }

    _resetAttributeSelections(attributeId) {
        const parsedAttributeId = parseInt(attributeId, 10);
        const attribute = this.state.ptalIds.find(
            (line) => line.id === parsedAttributeId
        );
        if (!attribute) {
            return;
        }

        for (const ptav of attribute.ptav_ids) {
            delete this.state.selected[ptav.id];
        }
    }

    async _validate() {
        const hasSelection = Object.keys(this.state.selected).length > 0;
        if (!hasSelection) {
            this.state.valid = false;
            this.state.errors = {};
            return;
        }

        const result = await rpc(`/cpq/${this.props.productTmplId}/validate`, {
            combination: this.state.selected,
        });

        this.state.valid = Boolean(result.valid);
        this.state.errors =
            result.errors && typeof result.errors === "object"
                ? result.errors
                : result.errors
                  ? {_global: result.errors}
                  : {};
    }

    async _onSelectAttribute(attributeId, valueId) {
        this._resetAttributeSelections(attributeId);

        const parsedValueId = parseInt(valueId, 10);
        if (!Number.isInteger(parsedValueId)) {
            await this._validate();
            return;
        }

        this.state.selected[parsedValueId] = null;
        await this._validate();
    }

    async _onCustomValue(ptavId, customValue) {
        const parsedPtavId = parseInt(ptavId, 10);
        if (!Number.isInteger(parsedPtavId)) {
            return;
        }
        if (!Object.prototype.hasOwnProperty.call(this.state.selected, parsedPtavId)) {
            return;
        }

        this.state.selected[parsedPtavId] = customValue;
        await this._validate();
    }

    async _onClickCreate() {
        if (!this.canCreate || this.state.creating) {
            return;
        }

        this.state.creating = true;
        try {
            const result = await rpc(`/cpq/${this.props.productTmplId}/configure`, {
                combination: this.state.selected,
            });

            if (this.props.save) {
                await this.props.save(result.product_tmpl_id, result.product_id);
            }
            this.props.close();
        } finally {
            this.state.creating = false;
        }
    }

    _onDiscard() {
        if (this.props.discard) {
            this.props.discard();
        }
        this.props.close();
    }

    get canCreate() {
        return this.state.valid && !this.state.creating;
    }
}

registry.category("actions").add("cpq.ConfigureDialogAction", (env, action) => {
    const context = action.context || {};
    if (context.active_model !== "product.template" || !context.active_id) {
        env.services.dialog.add(WarningDialog, {
            message: _lt(
                "The product configurator was somehow executed against something which is not a product template. Please contact support."
            ),
        });
        return;
    }

    env.services.dialog.add(ConfigureDialog, {
        productTmplId: context.active_id,
        save: (_, productId) =>
            env.services.action.doAction({
                type: "ir.actions.act_window",
                name: _t("Products"),
                res_model: "product.product",
                views: [[false, "form"]],
                res_id: productId,
            }),
    });
});
