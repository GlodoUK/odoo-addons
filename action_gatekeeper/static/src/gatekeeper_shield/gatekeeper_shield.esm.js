import {Component, useState} from "@odoo/owl";
import {GatekeeperShieldPopover} from "./gatekeeper_shield_popover.esm";
import {registry} from "@web/core/registry";
import {standardWidgetProps} from "@web/views/widgets/standard_widget_props";
import {usePopover} from "@web/core/popover/popover_hook";
import {useRecordObserver} from "@web/model/relational_model/utils";
import {useService} from "@web/core/utils/hooks";

const LINE_FIELDS = [
    "rule_name",
    "action",
    "is_released",
    "release_count",
    "release_count_required",
    "released_on",
    "can_release",
    "user_has_released",
    "release_request_target_ids",
];

export class GatekeeperShield extends Component {
    static template = "action_gatekeeper.GatekeeperShield";
    static props = {
        ...standardWidgetProps,
        inline: {type: Boolean, optional: true},
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({lines: []});
        this.popover = usePopover(GatekeeperShieldPopover, {
            position: "bottom-start",
        });
        useRecordObserver((record) => this.loadLines(record));
    }

    async loadLines(record = this.props.record) {
        if (!record.resId) {
            this.state.lines = [];
            return;
        }
        const [data] = await this.orm.read(
            record.resModel,
            [record.resId],
            ["gatekeeper_rule_lines"]
        );
        const ids = data ? data.gatekeeper_rule_lines : [];
        this.state.lines = ids.length
            ? await this.orm.read("gatekeeper.line", ids, LINE_FIELDS)
            : [];
    }

    get status() {
        const pending = this.state.lines.filter((line) => !line.is_released);
        if (pending.some((line) => line.action === "block")) {
            return "block";
        }
        if (pending.length) {
            return "hold";
        }
        return "released";
    }

    async refresh() {
        await Promise.all([this.loadLines(), this.props.record.load()]);
    }

    async onClick(ev) {
        if (this.popover.isOpen) {
            this.popover.close();
            return;
        }
        const target = ev.currentTarget;
        await this.loadLines();
        this.popover.open(target, {
            state: this.state,
            reload: this.refresh.bind(this),
        });
    }
}

export const gatekeeperShieldWidget = {
    component: GatekeeperShield,
    extractProps: ({options}) => ({
        inline: Boolean(options.inline),
    }),
};

registry.category("view_widgets").add("gatekeeper_shield", gatekeeperShieldWidget);
