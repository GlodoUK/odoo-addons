import {ActionPlugin} from "@web/webclient/actions/action_plugin";
import {ORM} from "@web/core/orm_plugin";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {usePlugin} from "@odoo/owl";

registry.category("command_setup").add("!", {
    debounceDelay: 200,
    emptyMessage: _t(
        "Search for the name of a record.\nIf you cannot find what you're looking for perhaps you need to configure the search providers?"
    ),
    name: _t("Record"),
    placeholder: _t("Search for a record..."),
});

registry.category("command_provider").add("model", {
    namespace: "!",
    async provide(options) {
        if (options.searchValue === undefined || options.searchValue.length < 2) {
            return [];
        }

        // Plugins must be acquired before any await, while the palette scope is active
        const orm = usePlugin(ORM);
        const action = usePlugin(ActionPlugin);
        const data = await orm.call("web.cmd.search.provider", "cmd_search", [
            options.searchValue,
        ]);
        const suggestion = [];

        for (const result of data) {
            suggestion.push({
                category: "cmd_search",
                name: result.name,
                action() {
                    action.doAction({
                        type: "ir.actions.act_window",
                        res_model: result.model,
                        res_id: result.id,
                        views: [[false, "form"]],
                        view_mode: "form",
                        target: "current",
                    });
                },
            });
        }

        return suggestion;
    },
});
