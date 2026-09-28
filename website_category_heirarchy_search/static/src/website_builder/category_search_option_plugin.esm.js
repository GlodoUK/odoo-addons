import {onWillStart, useState} from "@odoo/owl";
import {BaseOptionComponent} from "@html_builder/core/utils";
import {BuilderAction} from "@html_builder/core/builder_action";
import {Plugin} from "@html_editor/plugin";
import {registry} from "@web/core/registry";

// ─────────────────────────────────────────────────────────────────────────────
// Shared DOM helpers (used by actions and the drop handler)
// ─────────────────────────────────────────────────────────────────────────────

function rebuildPreviewSelects(snippetEl) {
    const labelsStr = snippetEl.dataset.levelLabels || "";
    const labels = labelsStr
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
    const fieldsEl = snippetEl.querySelector(".s_category_search_fields");
    if (!fieldsEl) return;

    fieldsEl.querySelectorAll(".s_category_search_level").forEach((el) => el.remove());
    const btn = fieldsEl.querySelector(".s_category_search_btn");

    for (let i = 0; i < labels.length; i++) {
        const level = document.createElement("div");
        level.className = "s_category_search_level";
        if (i > 0) level.classList.add("s_category_search_level_disabled");

        const select = document.createElement("select");
        select.className = "form-select";
        select.disabled = i > 0;
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = labels[i];
        select.appendChild(opt);

        level.appendChild(select);
        fieldsEl.insertBefore(level, btn);
    }
}

function syncButtonLabel(snippetEl) {
    const btn = snippetEl.querySelector(".s_category_search_btn");
    if (btn) btn.textContent = snippetEl.dataset.buttonLabel || "Find Parts";
}

// ─────────────────────────────────────────────────────────────────────────────
// Builder actions
// ─────────────────────────────────────────────────────────────────────────────

export class CategorySearchUpdateSelectsAction extends BuilderAction {
    static id = "categorySearchUpdateSelects";
    apply({editingElement}) {
        rebuildPreviewSelects(editingElement);
    }
}

export class CategorySearchUpdateButtonAction extends BuilderAction {
    static id = "categorySearchUpdateButton";
    apply({editingElement}) {
        syncButtonLabel(editingElement);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Option component
// ─────────────────────────────────────────────────────────────────────────────

export class CategorySearchOption extends BaseOptionComponent {
    static template = "website_category_heirarchy_search.CategorySearchOption";
    static selector = ".s_category_search";

    setup() {
        super.setup();
        this.state = useState({rootCategories: []});

        onWillStart(async () => {
            this.state.rootCategories = await this.services.orm.searchRead(
                "product.public.category",
                [["parent_id", "=", false]],
                ["id", "name"],
                {order: "name"}
            );
        });
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Plugin
// ─────────────────────────────────────────────────────────────────────────────

class CategorySearchOptionPlugin extends Plugin {
    static id = "categorySearchOption";

    resources = {
        builder_options: [CategorySearchOption],
        builder_actions: {
            CategorySearchUpdateSelectsAction,
            CategorySearchUpdateButtonAction,
        },
        on_snippet_dropped_handlers: this.onSnippetDropped.bind(this),
    };

    onSnippetDropped({snippetEl}) {
        if (!snippetEl.matches(".s_category_search")) return;
        rebuildPreviewSelects(snippetEl);
        syncButtonLabel(snippetEl);
    }
}

registry
    .category("website-plugins")
    .add(CategorySearchOptionPlugin.id, CategorySearchOptionPlugin);
