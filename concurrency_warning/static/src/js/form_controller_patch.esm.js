import {CONCURRENCY_RELOAD_EVENT} from "./poke_service.esm";
import {FormController} from "@web/views/form/form_controller";
import {patch} from "@web/core/utils/patch";
import {useBus} from "@web/core/utils/hooks";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        useBus(this.env.bus, CONCURRENCY_RELOAD_EVENT, ({detail}) => {
            const root = this.model.root;
            if (
                root?.resId &&
                root.resModel === detail.resModel &&
                root.resId === detail.resId
            ) {
                root.load();
                this.env.bus.trigger("MAIL:RELOAD-THREAD", {
                    model: detail.resModel,
                    id: detail.resId,
                });
            }
        });
    },
});
