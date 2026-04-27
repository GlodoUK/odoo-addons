import {CategorySearchWidget} from "@website_category_heirarchy_search/components/category_search_widget";
import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

export class CategorySearch extends Interaction {
    static selector = ".s_category_search";

    setup() {
        this.treeData = [];
        this.depth = 0;
        this.labels = [];
        this.initialSelected = [];
    }

    async willStart() {
        const rootCategoryName = this.el.dataset.rootCategory || "Vehicles";
        const result = await this.waitFor(
            rpc("/website_category_heirarchy_search/categories", {
                root_category_name: rootCategoryName,
            })
        );
        this.treeData = result.children || [];

        const labelsRaw = this.el.dataset.levelLabels || "";
        this.labels = labelsRaw
            ? labelsRaw
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
            : [];

        const treeDepth = result.depth || 0;
        this.depth =
            this.labels.length > 0
                ? Math.min(treeDepth, this.labels.length)
                : treeDepth;

        // Read any prior selections from the URL so the component can restore them.
        const params = new URLSearchParams(window.location.search);
        const vcats = params.get("vcats");
        if (vcats) {
            this.initialSelected = vcats
                .split(",")
                .map((n) => parseInt(n, 10) || null)
                .slice(0, this.depth);
        }
    }

    start() {
        const fieldsEl = this.el.querySelector(".s_category_search_fields");
        if (!fieldsEl) return;

        // Clear any static content saved by the builder preview (native selects,
        // static button) so the OWL component is the sole rendered widget.
        fieldsEl.innerHTML = "";

        const buttonLabel = this.el.dataset.buttonLabel || undefined;

        this.mountComponent(fieldsEl, CategorySearchWidget, {
            treeData: this.treeData,
            depth: this.depth,
            labels: this.labels,
            buttonLabel,
            initialSelected: this.initialSelected,
            onSearch: (selected) => this._onSearch(selected),
        });
    }

    _onSearch(selected) {
        // Most-specific (deepest non-null) selection determines the category filter.
        let categoryId = null;
        for (let i = selected.length - 1; i >= 0; i--) {
            if (selected[i]) {
                categoryId = selected[i];
                break;
            }
        }

        const shopUrl = this.el.dataset.shopUrl || "/shop";
        const params = new URLSearchParams();
        if (categoryId) params.set("category", categoryId);

        const nonNull = selected.filter(Boolean);
        if (nonNull.length) params.set("vcats", nonNull.join(","));

        window.location.href = `${shopUrl}?${params}`;
    }
}

registry
    .category("public.interactions")
    .add("website_category_heirarchy_search.category_search", CategorySearch);
