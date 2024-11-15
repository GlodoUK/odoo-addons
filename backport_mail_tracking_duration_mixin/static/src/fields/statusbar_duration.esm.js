/** @odoo-module **/

import {StatusBarField} from "@web/views/fields/statusbar/statusbar_field";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export function formatDuration(seconds, showFullDuration) {
    const displayStyle = showFullDuration ? "long" : "narrow";
    const numberOfValuesToDisplay = showFullDuration ? 2 : 1;
    const durationKeys = ["years", "months", "days", "hours", "minutes"];

    let secs = seconds;

    if (secs < 60) {
        secs = 60;
    }
    secs -= secs % 60;

    let duration = luxon.Duration.fromObject({seconds: secs}).shiftTo(...durationKeys);
    duration = duration.shiftTo(...durationKeys.filter((key) => duration.get(key)));
    const durationSplit = duration.toHuman({unitDisplay: displayStyle}).split(",");

    if (
        !showFullDuration &&
        duration.loc.locale.includes("en") &&
        duration.months > 0
    ) {
        durationSplit[0] = durationSplit[0].replace("m", "M");
    }
    return durationSplit.slice(0, numberOfValuesToDisplay).join(",");
}

export class StatusBarDurationField extends StatusBarField {
    computeItems() {
        const items = super.computeItems();
        const durationTracking = this.props.record.data.duration_tracking || {};
        if (Object.keys(durationTracking).length) {
            for (const item of items.unfolded) {
                const duration = durationTracking[item.id];
                if (duration > 0) {
                    item.shortTimeInStage = formatDuration(duration, false);
                    item.fullTimeInStage = formatDuration(duration, true);
                } else {
                    item.shortTimeInStage = 0;
                }
            }
        }
        return items;
    }
}

StatusBarDurationField.template =
    "backport_mail_tracking_duration_mixin.StatusBarDurationField";
StatusBarDurationField.displayName = _t("Status with time");
StatusBarDurationField.supportedTypes = ["many2one"];

StatusBarDurationField.props = {
    ...StatusBarField.props,
};

StatusBarDurationField.extractProps = StatusBarField.extractProps;
StatusBarDurationField.fieldDependencies = {
    duration_tracking: "JSON",
};

registry.category("fields").add("statusbar_duration", StatusBarDurationField);
