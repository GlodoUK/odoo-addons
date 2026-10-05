import {Component} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {formatDuration} from "@web/core/l10n/dates";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

export class StateDurationField extends Component {
    static template = "stock_picking_state_duration.StateDurationField";
    static props = {...standardFieldProps};

    get seconds() {
        return this.props.record.data[this.props.name];
    }

    get shortDuration() {
        return formatDuration(this.seconds, false);
    }

    get fullDuration() {
        return formatDuration(this.seconds, true);
    }
}

export const stateDurationField = {
    component: StateDurationField,
    displayName: _t("State Duration"),
    supportedTypes: ["integer"],
};

registry.category("fields").add("state_duration", stateDurationField);
