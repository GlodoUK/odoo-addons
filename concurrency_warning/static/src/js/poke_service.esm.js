import {_t} from "@web/core/l10n/translation";
import {debounce} from "@web/core/utils/timing";
import {registry} from "@web/core/registry";
import {user} from "@web/core/user";

export const concurrencyWarningService = {
    dependencies: ["bus_service", "notification", "action"],

    start(_env, {bus_service, notification: notification_service, action}) {
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

            const delNotification = notification_service.add(notification.message, {
                type: notification.type,
                sticky: notification.sticky || !notification.refresh,
                buttons: notification.refresh
                    ? undefined
                    : [
                          {
                              name: _t("Refresh"),
                              primary: true,
                              onClick: async () => {
                                  await action.doAction("soft_reload");
                                  delNotification();
                              },
                          },
                      ],
            });

            // Soft_reload
            if (notification.refresh) {
                action.doAction("soft_reload");
            }
        };
        bus_service.subscribe("poke/live_update", debounce(notify, 1000, true));
        bus_service.start();
    },
};

registry.category("services").add("concurrencyWarning", concurrencyWarningService);
