import {Component} from "@odoo/owl";
import {GatekeeperReleaseTargets} from "./gatekeeper_release_targets.esm";
import {_t} from "@web/core/l10n/translation";
import {useService} from "@web/core/utils/hooks";

export class GatekeeperShieldPopover extends Component {
    static template = "action_gatekeeper.GatekeeperShieldPopover";
    static components = {GatekeeperReleaseTargets};
    static props = {
        state: {type: Object},
        reload: {type: Function},
        close: {type: Function},
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async onRelease(line) {
        await this.orm.call("gatekeeper.line", "action_release", [[line.id]]);
        await this.props.reload();
    }

    async onRequestRelease(line) {
        await this.orm.call("gatekeeper.line", "action_request_release", [[line.id]]);
        this.notification.add(_t("Release request sent."), {
            type: "success",
        });
        await this.props.reload();
    }
}
