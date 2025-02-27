import {debounce} from "@web/core/utils/timing";
import {markup} from "@odoo/owl";
import {registry} from "@web/core/registry";

export const concurrencyWarningService = {
    dependencies: ["bus_service", "notification", "action"],

    start(env, {bus_service, notification: notificationService, action}) {
        const _doNotify = debounce(function (payload) {
            if (payload.refresh) {
                action.loadState();
            }

            const notificationRemove = notificationService.add(markup("Hello"), {
                title: "Hello",
                type: "Warning",
            });
        }, 1000);

        bus_service.subscribe("poke", (payload) => {
            // If (
            //     action.currentController.props.resModel === payload.model &&
            //     payload.ids.includes(action.currentController.props.resId) &&
            //     !action.currentController.view.multiRecord
            // ) {
            //     _doNotify(payload);
            // }
        });

        bus_service.start();
    },
};

registry.category("services").add("concurrency_warning", concurrencyWarningService);
