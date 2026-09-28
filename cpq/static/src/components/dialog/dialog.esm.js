import {Component, onWillStart, useState, xml} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {Notebook} from "@web/core/notebook/notebook";
import {WarningDialog} from "@web/core/errors/error_dialogs";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";
// eslint-disable-next-line sort-imports
import ProductTmplAttrib from "./product_tmpl_attrib.esm";

class CpqGroupPage extends Component {
    static template = xml`
        <div class="p-3">
            <ProductTmplAttrib
                t-foreach="props.ptalIds" t-as="line" t-key="line.id"
                id="line.id"
                attribute="line"
                selected="props.selected"
                onSelect="props.onSelect"
                onCustom="props.onCustom"
            />
        </div>
    `;
    static components = {ProductTmplAttrib};
    static props = {
        ptalIds: Array,
        selected: Object,
        onSelect: Function,
        onCustom: Function,
    };
}

export default class ConfigureDialog extends Component {
    static template = "cpq.ConfigureDialog";
    static components = {Dialog, ProductTmplAttrib, Notebook};
    static props = {
        productTmplId: Number,
        productId: {type: Number, optional: true},
        save: {type: Function, optional: true},
        discard: {type: Function, optional: true},
        combination: {type: Object, optional: true},
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

            if (this.props.combination && Object.keys(this.props.combination).length) {
                for (const [ptavId, customValue] of Object.entries(
                    this.props.combination
                )) {
                    const parsed = parseInt(ptavId, 10);
                    this.state.selected[parsed] = customValue ?? null;
                }
            } else {
                for (const ptal of this.state.ptalIds) {
                    if (ptal.ptav_ids.length === 1) {
                        this.state.selected[ptal.ptav_ids[0].id] = null;
                    }
                }
            }
            await this._validate();
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
        if (!this.canCreate) {
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

    get groups() {
        const groupMap = new Map();
        for (const ptal of this.state.ptalIds) {
            const gId = ptal.group_id || false;
            /* eslint-disable no-negated-condition */
            if (!groupMap.has(gId)) {
                groupMap.set(gId, {
                    id: gId,
                    name: ptal.group_name || _t("General"),
                    sequence:
                        ptal.group_sequence !== undefined ? ptal.group_sequence : 9999,
                    ptalIds: [],
                });
            }
            /* eslint-enable no-negated-condition */
            groupMap.get(gId).ptalIds.push(ptal);
        }
        return [...groupMap.values()].sort(
            (a, b) => a.sequence - b.sequence || (a.id || 0) - (b.id || 0)
        );
    }

    get notebookPages() {
        return this.groups.map((group) => ({
            Component: CpqGroupPage,
            id: String(group.id || "general"),
            title: group.name,
            props: {
                ptalIds: group.ptalIds,
                selected: this.state.selected,
                onSelect: (attributeId, valueId) =>
                    this._onSelectAttribute(attributeId, valueId),
                onCustom: (ptavId, value) => this._onCustomValue(ptavId, value),
            },
        }));
    }
}

registry.category("actions").add("cpq.ConfigureDialogAction", (env, action) => {
    const context = action.context || {};
    if (context.active_model !== "product.template" || !context.active_id) {
        env.services.dialog.add(WarningDialog, {
            message: _t(
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
