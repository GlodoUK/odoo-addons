/** @odoo-module **/
/* eslint-disable sort-imports */

import {Dialog} from "@web/core/dialog/dialog";
import {WarningDialog} from "@web/core/errors/error_dialogs";
import {_lt} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
const {onWillStart, useState} = owl.hooks;
import ProductTmplAttrib from "./product_tmpl_attrib.esm";

import {useHotkey} from "@web/core/hotkeys/hotkey_hook";

export default class ConfigureDialog extends Dialog {
    setup() {
        super.setup();

        this.rpc = useService("rpc");
        this.state = useState({
            ptalIds: [],
            selected: {},
            productTmplId: {},
            valid: false,
            errors: {},
        });

        useHotkey("escape", () => {
            this._onDiscard();
        });

        onWillStart(async () => {
            const data = await this._loadData();
            this.title = _.str.sprintf(
                this.env._t("Configure: %s"),
                data.product_tmpl_id.display_name
            );
            this.state.ptalIds = data.ptal_ids;
            this.state.productTmplId = data.product_tmpl_id;
        });
    }

    async _loadData() {
        return this.rpc(`/cpq/${this.props.productTmplId}/data`, {});
    }

    async _validate() {
        if (this.state.selected) {
            this.rpc(`/cpq/${this.props.productTmplId}/validate`, {
                combination: this.state.selected,
            }).then((res) => {
                this.state.valid = res.valid;
                this.state.errors = res.errors;
            });
        }
    }

    _onDiscard() {
        if (this.props.discard) {
            this.props.discard();
        }

        this.close();
    }

    _onClickCreate() {
        const combination = this.state.selected;

        return this.rpc(`/cpq/${this.props.productTmplId}/configure`, {
            combination: combination,
        }).then((res) => {
            if (this.props.save) {
                this.props.save(res.product_tmpl_id, res.product_id);
            }

            this.close();
        });
    }

    _addOrUpdateSelected(attributeId, valueId, customValue) {
        const parsedValueId = parseInt(valueId, 10);
        const parsedAttribId = parseInt(attributeId, 10);

        const attribute = this.state.ptalIds.find((e) => e.id === parsedAttribId);
        if (!attribute) {
            return;
        }

        attribute.ptav_ids
            .map((e) => {
                return e.id;
            })
            .forEach((e) => {
                delete this.state.selected[e];
            });

        const attributeValue = attribute.ptav_ids.find((e) => {
            return e.id === parsedValueId;
        });

        if (attributeValue) {
            this.state.selected[parsedValueId] = null;
        }

        if (attributeValue && attributeValue.is_custom && customValue !== undefined) {
            this.state.selected[parsedValueId] = customValue;
        }

        this._validate();
    }

    get canCreate() {
        if (!this.state.ptalIds) {
            return false;
        }

        return this.state.valid;
    }

    stringify() {
        return JSON.stringify(this.state);
    }
}

ConfigureDialog.template = "cpq.ConfigureDialogDialog";
ConfigureDialog.footerTemplate = "cpq.ConfigureDialogFooter";
ConfigureDialog.footerTemplate = "cpq.ConfigureDialogFooter";
ConfigureDialog.bodyTemplate = "cpq.ConfigureDialogBody";
ConfigureDialog.components = Object.assign({}, Dialog.components, {ProductTmplAttrib});
ConfigureDialog.title = "Configure";

registry.category("actions").add("cpq.ConfigureDialogAction", function (env, data) {
    if (data.context.active_model !== "product.template" || !data.context.active_id) {
        env.services.dialog.add(WarningDialog, {
            message: _lt(
                "The product configurator was somehow executed against something which is not a product template. Please contact support."
            ),
        });
        return;
    }

    env.services.dialog.add(ConfigureDialog, {
        productTmplId: data.context.active_id,
        save: (productTmplId, productId) => {
            return env.services.action.doAction({
                type: "ir.actions.act_window",
                name: env._t("Products"),
                res_model: "product.product",
                views: [[false, "form"]],
                res_id: productId,
            });
        },
    });
});
