import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardActionServiceProps} from "@web/webclient/actions/action_service";

// The app's landing: a static explainer, so opening Autopilot lands somewhere
// meaningful rather than an arbitrary connector. The actual work lives in the
// per-connector menus a connector adds under the Autopilot app.
export class AutopilotOverview extends Component {
    static template = "autopilot.Overview";
    static props = {...standardActionServiceProps};
}

registry.category("actions").add("autopilot_overview", AutopilotOverview);
