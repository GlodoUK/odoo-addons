/** @odoo-module **/
/* eslint-disable sort-imports */

import {_t} from "@web/core/l10n/translation";
import {Dialog} from "@web/core/dialog/dialog";
import {Component, onWillStart, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {WarningDialog} from "@web/core/errors/error_dialogs";
import ProductTmplAttrib from "./product_tmpl_attrib.esm";

export class ConfigureDialog extends Component {
    static components = {Dialog, ProductTmplAttrib};
    static props = {
        productTmplId: Number,
        save: Function,
        close: Function,
        edit: Boolean,
        discard: Function,
    };
    static template = "cpq.ConfigureDialogDialog";
    setup() {
        this.size = "xl";
        this.rpc = useService("rpc");
        this.state = useState({
            ptalIds: [],
            selected: {},
            productTmplId: null,
            valid: false,
            errors: {},
        });

        onWillStart(async () => {
            const data = await this._loadData();
            this.title = _t("Configure: %s", data.product_tmpl_id.display_name);
            this.state.ptalIds = data.ptal_ids;
            this.state.productTmplId = data.product_tmpl_id;
        });
    }

    async _loadData() {
        return this.rpc(`/cpq/${this.props.productTmplId}/data`, {});
    }

    canCreate() {
        if (!this.state.ptalIds) {
            return false;
        }

        return this.state.valid;
    }

    onCreate() {
        const combination = this.state.selected;

        return this.rpc(`/cpq/${this.props.productTmplId}/configure`, {
            combination: combination,
        }).then((res) => {
            if (this.props.save) {
                this.props.save(res.product_tmpl_id, res.product_id);
            }

            this.onClose();
        });
    }

    onClose() {
        // Reset the state
        this.state.ptalIds = [];
        this.state.selected = {};
        this.state.productTmplId = null;
        this.state.valid = false;
        this.state.errors = {};

        if (this.props.discard) {
            this.props.discard();
        }

        this.props.close();
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

    _addOrUpdateSelected(attributeId, valueId, customValue) {
        const parsedValueId = parseInt(valueId, 10);
        const parsedAttribId = parseInt(attributeId, 10);

        const attribute = this.state.ptalIds.find((e) => e.id === parsedAttribId);

        if (!attribute) {
            return;
        }

        const newSelected = {...this.state.selected};

        attribute.ptav_ids
            .map((e) => {
                return e.id;
            })
            .forEach((e) => {
                // Check if e.id already exists as a key and delete it if it does from newSelected
                if (e in newSelected) {
                    delete newSelected[e];
                }
            });

        // Find the attribute value
        const attributeValue = attribute.ptav_ids.find((e) => e.id === parsedValueId);

        if (attributeValue) {
            newSelected[parsedValueId] = attributeValue.name;
        }

        if (attributeValue && attributeValue.is_custom && customValue !== undefined) {
            newSelected[parsedValueId] = customValue;
        }

        this.state.selected = newSelected;

        this._validate();
    }
}

export function ConfigureDialogAction(env, action) {
    if (
        action.context.active_model !== "product.template" ||
        !action.context.active_id
    ) {
        env.services.dialog.add(WarningDialog, {
            body: _t(
                "The product configurator was somehow executed against something which is not a product template. Please contact support."
            ),
            confirm: () => {
                return env.services.action.doAction({
                    type: "ir.actions.act_window_close",
                });
            },
        });
    }
    env.services.dialog.add(ConfigureDialog, {
        productTmplId: action.context.active_id,
        edit: true,
        save: (productTmplId, productId) => {
            return env.services.action.doAction({
                type: "ir.actions.act_window",
                res_model: "product.product",
                views: [[false, "form"]],
                res_id: productId,
            });
        },

        close: () => {
            return env.services.action.doAction({type: "ir.actions.act_window_close"});
        },
        discard: () => {
            return env.services.action.doAction({type: "ir.actions.act_window_close"});
        },
    });
}

registry.category("actions").add("cpq.ConfigureDialogAction", ConfigureDialogAction);
