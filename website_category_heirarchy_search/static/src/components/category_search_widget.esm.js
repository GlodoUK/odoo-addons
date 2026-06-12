import {Component, onWillStart, useState, xml} from "@odoo/owl";
import {SelectMenu} from "@web/core/select_menu/select_menu";
import {rpc} from "@web/core/network/rpc";

export class CategorySearchWidget extends Component {
    static components = {SelectMenu};

    static props = {
        treeData: Array,
        depth: Number,
        labels: Array,
        buttonLabel: {type: String, optional: true},
        initialSelected: {type: Array, optional: true},
        onSearch: Function,
    };

    // Inline OWL template — one SelectMenu per level, then the search button.
    static template = xml`
        <t t-foreach="levelData" t-as="level" t-key="level_index">
            <div t-att-class="'s_category_search_level' + (level.enabled ? '' : ' s_category_search_level_disabled')">
                <SelectMenu
                    choices="level.choices"
                    value="state.selected[level_index]"
                    onSelect="(v) => this.onLevelSelect(level_index, v)"
                    placeholder="this.getLabel(level_index)"
                />
            </div>
        </t>
        <button type="button" class="btn btn-primary s_category_search_btn" t-on-click="onSearch">
            <t t-esc="props.buttonLabel || 'Find Parts'"/>
        </button>
    `;

    setup() {
        // Seed selections from URL restore data, padded/trimmed to exact depth.
        const init = (this.props.initialSelected || []).slice(0, this.props.depth);
        while (init.length < this.props.depth) init.push(null);

        // Counts is a stringified cat id → count
        this.state = useState({
            selected: init,
            counts: {},
        });

        onWillStart(async () => {
            // Fetch counts for all items visible at initial render in one batch.
            const ids = this._preloadIds();
            if (ids.length) {
                const counts = await rpc("/website_category_heirarchy_search/counts", {
                    category_ids: ids,
                });
                Object.assign(this.state.counts, counts);
            }
        });
    }

    // -------------------------------------------------------------------------
    // Derived data consumed by the template
    // -------------------------------------------------------------------------

    /**
     * Returns one entry per level: { choices, enabled }.
     * Re-evaluated reactively whenever state.selected or state.counts change.
     */
    get levelData() {
        const result = [];
        let items = this.props.treeData;

        for (let i = 0; i < this.props.depth; i++) {
            const choices = items.map((item) => ({
                value: item.id,
                label: this._labelFor(item),
            }));

            result.push({choices, enabled: items.length > 0});

            const selectedId = this.state.selected[i];
            if (selectedId) {
                const found = items.find((x) => x.id === selectedId);
                items = found ? found.children : [];
            } else {
                // No selection at this level — fill remaining levels as empty.
                for (let j = i + 1; j < this.props.depth; j++) {
                    result.push({choices: [], enabled: false});
                }
                break;
            }
        }

        return result;
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    getLabel(levelIndex) {
        return this.props.labels[levelIndex] || `Select level ${levelIndex + 1}`;
    }

    _labelFor(item) {
        const count = this.state.counts[String(item.id)];
        return count === undefined ? item.name : `${item.name} (${count})`;
    }

    /** IDs of all items that need counts on the initial render. */
    _preloadIds() {
        const ids = this.props.treeData.map((x) => x.id);
        let items = this.props.treeData;
        for (let i = 0; i < this.props.depth; i++) {
            const id = this.state.selected[i];
            if (!id) break;
            const item = items.find((x) => x.id === id);
            if (!item) break;
            ids.push(...item.children.map((c) => c.id));
            items = item.children;
        }
        return ids;
    }

    _findItem(id, level) {
        let items = this.props.treeData;
        for (let i = 0; i < level; i++) {
            const parent = items.find((x) => x.id === this.state.selected[i]);
            if (!parent) return null;
            items = parent.children;
        }
        return items.find((x) => x.id === id) || null;
    }

    // -------------------------------------------------------------------------
    // Event handlers
    // -------------------------------------------------------------------------

    async onLevelSelect(level, value) {
        const id = value || null;
        const newSelected = [...this.state.selected];
        newSelected[level] = id;
        for (let i = level + 1; i < this.props.depth; i++) newSelected[i] = null;
        this.state.selected = newSelected;

        // Fetch counts for the newly revealed level's items.
        if (id) {
            const item = this._findItem(id, level);
            if (item && item.children.length) {
                const counts = await rpc("/website_category_heirarchy_search/counts", {
                    category_ids: item.children.map((c) => c.id),
                });
                Object.assign(this.state.counts, counts);
            }
        }
    }

    onSearch() {
        this.props.onSearch([...this.state.selected]);
    }
}
