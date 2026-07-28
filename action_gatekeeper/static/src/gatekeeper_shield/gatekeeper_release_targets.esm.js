import {Component, onWillStart, useState} from "@odoo/owl";
import {usePopover} from "@web/core/popover/popover_hook";
import {useService} from "@web/core/utils/hooks";

const MAX_VISIBLE_AVATARS = 3;

export class GatekeeperReleaseTargetsPopover extends Component {
    static template = "action_gatekeeper.GatekeeperReleaseTargetsPopover";
    static props = {
        users: {type: Array},
        close: {type: Function},
    };

    avatarUrl(user) {
        return `/web/image/res.users/${user.id}/avatar_128`;
    }
}

export class GatekeeperReleaseTargets extends Component {
    static template = "action_gatekeeper.GatekeeperReleaseTargets";
    static props = {
        userIds: {type: Array},
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({users: []});
        this.popover = usePopover(GatekeeperReleaseTargetsPopover);

        onWillStart(() => this.loadUsers());
    }

    async loadUsers() {
        this.state.users = this.props.userIds.length
            ? await this.orm.read("res.users", this.props.userIds, ["name"])
            : [];
    }

    get visibleUsers() {
        return this.state.users.slice(0, MAX_VISIBLE_AVATARS);
    }

    get extraCount() {
        return Math.max(0, this.state.users.length - MAX_VISIBLE_AVATARS);
    }

    avatarUrl(user) {
        return `/web/image/res.users/${user.id}/avatar_128`;
    }

    onClick(ev) {
        if (this.popover.isOpen) {
            this.popover.close();
            return;
        }
        const target = ev.currentTarget;
        this.popover.open(target, {users: this.state.users});
    }
}
