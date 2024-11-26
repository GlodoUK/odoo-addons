/** @odoo-module **/

import {debounce} from "@web/core/utils/timing";
import {registry} from "@web/core/registry";

const concurrencyWarning = {
    dependencies: ["action", "notification", "user"],

    _willDelete() {
        if (this.env.services.bus_service) {
            this.env.services.bus_service.off("notification");
            this.env.services.bus_service.stopPolling();
        }
        return super._willDelete(...arguments);
    },

    start(env, {action, notification, user}) {
        const _doNotify = debounce(function (payload) {
            notification.add(
                _.str.sprintf(
                    env._t(
                        "This record has been changed by another user (%s) since you opened it. The record has been automatically refreshed."
                    ),
                    payload.username
                ),
                {
                    title: env._t("Record changed"),
                    type: "warning",
                    sticky: false,
                }
            );

            action.loadState();
        }, 1000);

        function _handleNotifications(notifications) {
            for (const {payload, type} of notifications) {
                if (type !== "poke") {
                    continue;
                }

                if (
                    !action ||
                    !action.currentController ||
                    user.userId === payload.uid
                ) {
                    continue;
                }

                if (
                    action.currentController.props.resModel === payload.model &&
                    payload.ids.includes(action.currentController.props.resId) &&
                    !action.currentController.view.multiRecord
                ) {
                    _doNotify(payload);
                }
            }
        }

        env.bus.on("WEB_CLIENT_READY", null, async () => {
            const legacyEnv = owl.Component.env;

            legacyEnv.services.bus_service.onNotification(this, _handleNotifications);
            legacyEnv.services.bus_service.startPolling();
        });
    },
};

registry.category("services").add("concurrencyWarning", concurrencyWarning);
