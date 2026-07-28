import {Component, onWillStart, onWillUpdateProps, useState} from "@odoo/owl";
import {GatekeeperShieldPopover} from "./gatekeeper_shield_popover.esm";
import {registry} from "@web/core/registry";
import {standardWidgetProps} from "@web/views/widgets/standard_widget_props";
import {usePopover} from "@web/core/popover/popover_hook";
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
    static props = {...standardWidgetProps};

    setup() {
        this.orm = useService("orm");
        this.state = useState({lines: []});
        this.popover = usePopover(GatekeeperShieldPopover, {
            position: "bottom-start",
        });

        onWillStart(() => this.loadLines());
        onWillUpdateProps((nextProps) => {
            if (nextProps.record.resId !== this.props.record.resId) {
                return this.loadLines(nextProps.record);
            }
        });
    }

    async loadLines(record = this.props.record) {
        if (!record.resId) {
            this.state.lines = [];
            return;
        }
        // Read the record's own gatekeeper_rule_lines relation rather than
        // searching gatekeeper.line by res_model/res_id directly, so stale
        // lines that were unlinked from the record (but not yet cleaned up
        // in the database) never show up here.
        const [data] = await this.orm.read(
            record.resModel,
            [record.resId],
            ["gatekeeper_rule_lines"]
        );
        const ids = data.gatekeeper_rule_lines;
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
        // Ev.currentTarget is nulled out once the event finishes
        // dispatching, so it must be captured before the await below,
        // not read afterwards.
        const target = ev.currentTarget;
        // The widget isn't guaranteed to re-render (and thus reload) when
        // the record is saved/reloaded elsewhere on the form (e.g. via a
        // statusbar button such as Cancel or Reset to Quotation), so
        // always fetch fresh data at the moment the user opens this.
        await this.loadLines();
        this.popover.open(target, {
            state: this.state,
            reload: this.refresh.bind(this),
        });
    }
}

export const gatekeeperShieldWidget = {
    component: GatekeeperShield,
};

registry.category("view_widgets").add("gatekeeper_shield", gatekeeperShieldWidget);
