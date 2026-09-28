import {_t} from "@web/core/l10n/translation";
import {debounce} from "@web/core/utils/timing";
import {registry} from "@web/core/registry";
import {user} from "@web/core/user";

export const CONCURRENCY_RELOAD_EVENT = "CONCURRENCY_WARNING:RELOAD_RECORD";

export const concurrencyWarningService = {
    dependencies: ["bus_service", "notification", "action"],

    start(env, {bus_service, notification: notification_service, action}) {
        const notify = (notification) => {
            const controller = action.currentController;
            if (notification.userId === user.userId) {
                return;
            }
            const viewing =
                controller?.props?.resModel === notification.resModel &&
                controller?.props?.resId === notification.resId;
            if (!viewing) {
                return;
            }

            const reload = () =>
                env.bus.trigger(CONCURRENCY_RELOAD_EVENT, {
                    resModel: notification.resModel,
                    resId: notification.resId,
                });

            const delNotification = notification_service.add(notification.message, {
                type: notification.type,
                sticky: notification.sticky || !notification.refresh,
                buttons: notification.refresh
                    ? undefined
                    : [
                          {
                              name: _t("Refresh"),
                              primary: true,
                              onClick: () => {
                                  reload();
                                  delNotification();
                              },
                          },
                      ],
            });

            if (notification.refresh) {
                reload();
            }
        };
        bus_service.subscribe("poke/live_update", debounce(notify, 1000, true));
        bus_service.start();
    },
};

registry.category("services").add("concurrencyWarning", concurrencyWarningService);
