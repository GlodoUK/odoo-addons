/** @odoo-module **/
import {debounce} from "@web/core/utils/timing";
import {registry} from "@web/core/registry";

export const concurrencyWarningService = {
    dependencies: ["bus_service", "notification", "action", "user"],

    start(env, {bus_service, notification, action, user}) {
        const _doNotify = debounce(function (payload) {
            if (payload.refresh) {
                action.loadState();
            }

            notification.add(payload.msg, {
                title: env._t("Record changed"),
                type: payload.type || "warning",
                sticky: payload.sticky || false,
            });
        }, 1000);

        bus_service.addEventListener("notification", ({detail: notifications}) => {
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
        });
        bus_service.start();
    },
};

registry.category("services").add("concurrencyWarning", concurrencyWarningService);
