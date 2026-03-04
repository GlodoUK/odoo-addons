import {CONCURRENCY_RELOAD_EVENT} from "./poke_service.esm";

import {FormController} from "@web/views/form/form_controller";

import {useBus} from "@web/core/utils/hooks";
import {patch} from "@web/core/utils/patch";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        useBus(this.env.bus, CONCURRENCY_RELOAD_EVENT, () => {
            if (this.model.root?.resId) {
                this.model.root.load();
            }
        });
    },
});
