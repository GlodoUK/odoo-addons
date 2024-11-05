/** @odoo-module **/

import {_lt} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

registry.category("command_setup").add("!", {
    debounceDelay: 200,
    emptyMessage: _lt(
        "Search for the name of a record.\nIf you cannot find what you're looking for perhaps you need to configure the search providers?"
    ),
    name: _lt("Record"),
    placeholder: _lt("Search for a record..."),
});

registry.category("command_provider").add("model", {
    namespace: "!",
    async provide(env, options) {
        if (options.searchValue === undefined || options.searchValue.length < 2) {
            return [];
        }

        const data = await env.services.orm.call(
            "web.cmd.search.provider",
            "cmd_search",
            [options.searchValue]
        );
        const suggestion = [];

        for (const result of data) {
            suggestion.push({
                category: "cmd_search",
                name: result.name,
                action() {
                    env.services.action.doAction({
                        type: "ir.actions.act_window",
                        res_model: result.model,
                        res_id: result.id,
                        views: [[false, "form"]],
                    });
                },
            });
        }

        return suggestion;
    },
});
